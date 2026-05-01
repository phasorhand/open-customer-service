from opencs.agents.base_worker import BaseWorker, WorkerInput
from opencs.channel.exec_token import ExecutionToken
from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import ContentPart, InboundMessage, OutboundAction
from opencs.harness.action_guard import ActionGuard, ActionGuardDecision
from opencs.harness.action_plan import ActionPlan


class Orchestrator:
    """Receives InboundMessage, delegates to Workers, runs plans through ActionGuard.

    For auto-approved `channel.send` plans: immediately executes via ChannelAdapter.
    For HITL-queued plans: leaves them in HITLQueue for human review.
    """

    def __init__(
        self,
        *,
        workers: list[BaseWorker],
        guard: ActionGuard,
        registry: ChannelRegistry,
    ) -> None:
        self._workers = workers
        self._guard = guard
        self._registry = registry

    async def handle(self, *, message: InboundMessage) -> None:
        inp = WorkerInput(message=message)
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
