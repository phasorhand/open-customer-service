from __future__ import annotations

from collections.abc import Callable as _Callable
from datetime import UTC, datetime
from functools import wraps
from typing import TYPE_CHECKING
from typing import Any as _Any

from opencs.agents.base_worker import BaseWorker, WorkerInput
from opencs.channel.exec_token import ExecutionToken
from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import ContentPart, InboundMessage, OutboundAction
from opencs.harness.action_guard import ActionGuard, ActionGuardDecision
from opencs.harness.action_plan import ActionPlan
from opencs.memory.l0_store import L0Event

if TYPE_CHECKING:
    from opencs.memory.memory_store import MemoryStore
    from opencs.skills.skill_repo import SkillRepo
    from opencs.tools.executor import ToolExecutor


def _observe(name: str) -> _Callable[..., _Any]:
    """Decorator: wraps coroutine with Langfuse @observe if available; else no-op."""
    dec: _Callable[..., _Any]
    try:
        from langfuse.decorators import observe as lf_observe
        dec = lf_observe(name=name)
    except Exception:
        def _noop(fn: _Callable[..., _Any]) -> _Callable[..., _Any]:
            @wraps(fn)
            async def wrapped(*a: _Any, **kw: _Any) -> _Any:
                return await fn(*a, **kw)
            return wrapped
        dec = _noop

    def outer(fn: _Callable[..., _Any]) -> _Callable[..., _Any]:
        wrapped: _Any = dec(fn)
        wrapped.__langfuse_observed__ = True
        return wrapped  # type: ignore[no-any-return]

    return outer


class Orchestrator:
    """Receives InboundMessage, loads memory + skills, delegates to Workers, guards plans.

    For auto-approved `channel.send` plans: immediately executes via ChannelAdapter.
    For auto-approved tool plans: dispatches to ToolExecutor, logs result to L0.
    For HITL-queued plans: leaves them in HITLQueue for human review.
    """

    def __init__(
        self,
        *,
        workers: list[BaseWorker],
        guard: ActionGuard,
        registry: ChannelRegistry,
        memory_store: MemoryStore | None = None,
        skill_repo: SkillRepo | None = None,
        tool_executor: ToolExecutor | None = None,
    ) -> None:
        self._workers = workers
        self._guard = guard
        self._registry = registry
        self._memory = memory_store
        self._skills = skill_repo
        self._tool_executor = tool_executor

    @_observe(name="conversation.handle")
    async def handle(self, *, message: InboundMessage) -> None:
        if self._memory:
            self._memory.record_inbound(message)

        session_context: dict[str, object] = {}
        if self._memory:
            ctx = self._memory.load_context(
                message.conversation_id,
                customer_id=message.customer_id,
                message_text=message.text_concat(),
            )
            session_context.update(ctx)

        if self._skills:
            session_context["skills"] = self._skills.match(message.text_concat())

        inp = WorkerInput(message=message, session_context=session_context)
        all_plans: list[ActionPlan] = []
        for worker in self._workers:
            plans = await worker.run(inp)
            all_plans.extend(plans)

        for plan in all_plans:
            outcome = self._guard.evaluate(plan)
            if outcome.decision == ActionGuardDecision.AUTO_APPROVED and outcome.token:
                await self._execute_plan(
                    plan, token=outcome.token, conversation_id=message.conversation_id
                )

    async def _execute_plan(
        self, plan: ActionPlan, *, token: ExecutionToken, conversation_id: str
    ) -> None:
        if plan.tool_id == "channel.send":
            conv_id = str(plan.args["conversation_id"])
            text = str(plan.args["text"])
            channel_id = str(plan.args.get("channel_id", "webchat"))
            try:
                adapter = self._registry.get(channel_id)
            except Exception:
                adapter = self._registry.get("webchat")
            action = OutboundAction(
                conversation_id=conv_id,
                kind="reply",
                content=[ContentPart(kind="text", text=text)],
                target=None,
                metadata={"action_id": plan.action_id},
            )
            await adapter.send(action, token)
            return

        if self._tool_executor is None:
            return

        if self._memory:
            self._memory.l0.append(L0Event(
                conversation_id=conversation_id,
                kind="tool_call",
                payload={
                    "action_id": plan.action_id,
                    "tool_id": plan.tool_id,
                    "args": dict(plan.args),
                },
                ts=datetime.now(UTC),
            ))

        result = await self._tool_executor.execute(plan, token)

        if self._memory:
            self._memory.l0.append(L0Event(
                conversation_id=conversation_id,
                kind="tool_result",
                payload={
                    "action_id": plan.action_id,
                    "tool_id": plan.tool_id,
                    "success": result.success,
                    "data": result.data,
                    "error": result.error,
                },
                ts=datetime.now(UTC),
            ))
