from opencs.agents.base_worker import BaseWorker, WorkerInput
from opencs.harness.action_plan import ActionPlan


class ApprovalRouterWorker(BaseWorker):
    """Phase-2 stub. Phase 7 adds HITL routing logic."""

    worker_id = "approval_router"

    async def run(self, inp: WorkerInput) -> list[ActionPlan]:
        return []
