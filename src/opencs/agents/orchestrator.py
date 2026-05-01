from __future__ import annotations

from typing import TYPE_CHECKING

from opencs.agents.base_worker import BaseWorker, WorkerInput
from opencs.channel.exec_token import ExecutionToken
from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import ContentPart, InboundMessage, OutboundAction
from opencs.harness.action_guard import ActionGuard, ActionGuardDecision
from opencs.harness.action_plan import ActionPlan

if TYPE_CHECKING:
    from opencs.memory.memory_store import MemoryStore
    from opencs.skills.skill_repo import SkillRepo


class Orchestrator:
    """Receives InboundMessage, loads memory + skills, delegates to Workers, guards plans.

    For auto-approved `channel.send` plans: immediately executes via ChannelAdapter.
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
    ) -> None:
        self._workers = workers
        self._guard = guard
        self._registry = registry
        self._memory = memory_store
        self._skills = skill_repo

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
                await self._execute_plan(plan, token=outcome.token)

    async def _execute_plan(self, plan: ActionPlan, *, token: ExecutionToken) -> None:
        if plan.tool_id != "channel.send":
            return  # ToolProvider integration deferred to Phase 4

        conversation_id = str(plan.args["conversation_id"])
        text = str(plan.args["text"])

        # Use channel_id from args if provided, fall back to webchat
        channel_id = str(plan.args.get("channel_id", "webchat"))
        try:
            adapter = self._registry.get(channel_id)
        except Exception:
            adapter = self._registry.get("webchat")

        action = OutboundAction(
            conversation_id=conversation_id,
            kind="reply",
            content=[ContentPart(kind="text", text=text)],
            target=None,
            metadata={"action_id": plan.action_id},
        )
        await adapter.send(action, token)
