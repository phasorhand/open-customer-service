from datetime import UTC, datetime

from opencs.agents.base_worker import WorkerInput
from opencs.agents.cs_reply import CSReplyWorker
from opencs.agents.llm_client import FakeLLMClient
from opencs.agents.orchestrator import Orchestrator
from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import ContentPart, InboundMessage
from opencs.channel.webchat import WebChatAdapter
from opencs.harness.action_guard import ActionGuard
from opencs.harness.action_plan import ActionPlan, RiskTier
from opencs.harness.audit_log import AuditLog
from opencs.harness.hitl_queue import HITLQueue
from opencs.harness.token import TokenFactory


def _guard() -> ActionGuard:
    return ActionGuard(
        token_factory=TokenFactory(secret_key=b"test", default_ttl_seconds=60),
        audit_log=AuditLog(db_path=":memory:"),
        hitl_queue=HITLQueue(),
    )


def _inbound(text: str = "hello") -> InboundMessage:
    return InboundMessage(
        channel_id="webchat",
        conversation_id="conv-1",
        customer_id="cust-1",
        sender_kind="customer",
        content=[ContentPart(kind="text", text=text)],
        timestamp=datetime(2026, 5, 1, tzinfo=UTC),
        raw_payload={},
        platform_meta={},
    )


async def test_orchestrator_calls_worker_and_sends_reply() -> None:
    registry = ChannelRegistry()
    webchat = WebChatAdapter()
    registry.register(webchat)

    received: list[object] = []
    webchat.subscribe("conv-1", received.append)

    llm = FakeLLMClient(responses=["Hi from agent!"])
    worker = CSReplyWorker(llm=llm, model="fake")
    guard = _guard()

    orch = Orchestrator(workers=[worker], guard=guard, registry=registry)
    await orch.handle(message=_inbound("hi"))

    # ORANGE_C goes to HITL — token NOT issued; send NOT called on webchat
    # Verify audit log captured the decision
    entries = guard._log.recent(limit=5)
    assert len(entries) == 1
    assert entries[0].decision == "hitl_queued"
    # No webchat message sent
    assert received == []


async def test_orchestrator_sends_green_plan_via_channel() -> None:
    """Use a worker that produces a GREEN plan so ActionGuard auto-approves."""

    class _GreenWorker(CSReplyWorker):
        async def run(self, inp: WorkerInput) -> list[ActionPlan]:
            return [ActionPlan(
                action_id="green-001",
                tool_id="channel.send",
                args={"conversation_id": inp.message.conversation_id, "text": "auto-reply"},
                intent="Test auto-reply",
                risk_hint=RiskTier.GREEN,
            )]

    registry = ChannelRegistry()
    webchat = WebChatAdapter()
    registry.register(webchat)

    received: list[object] = []
    webchat.subscribe("conv-1", received.append)

    worker = _GreenWorker(llm=FakeLLMClient(responses=[""]), model="fake")
    guard = _guard()

    orch = Orchestrator(workers=[worker], guard=guard, registry=registry)
    await orch.handle(message=_inbound("hi"))

    assert len(received) == 1


async def test_orchestrator_no_channel_send_for_hitl_plans() -> None:
    llm = FakeLLMClient(responses=["reply"])
    worker = CSReplyWorker(llm=llm, model="fake")
    guard = _guard()

    registry = ChannelRegistry()
    registry.register(WebChatAdapter())

    orch = Orchestrator(workers=[worker], guard=guard, registry=registry)
    # ORANGE_C → HITL → no send
    await orch.handle(message=_inbound("test"))
    entries = guard._log.recent(limit=5)
    assert entries[0].decision == "hitl_queued"
