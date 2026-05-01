from datetime import UTC, datetime

from opencs.agents.approval_router import ApprovalRouterWorker
from opencs.agents.base_worker import WorkerInput
from opencs.channel.schema import ContentPart, InboundMessage


def _inbound() -> InboundMessage:
    return InboundMessage(
        channel_id="webchat",
        conversation_id="c1",
        customer_id="u1",
        sender_kind="customer",
        content=[ContentPart(kind="text", text="help")],
        timestamp=datetime(2026, 5, 1, tzinfo=UTC),
        raw_payload={},
        platform_meta={},
    )


async def test_approval_router_stub_returns_empty() -> None:
    worker = ApprovalRouterWorker()
    plans = await worker.run(WorkerInput(message=_inbound()))
    assert plans == []


def test_approval_router_has_worker_id() -> None:
    assert ApprovalRouterWorker.worker_id == "approval_router"
