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


async def test_orchestrator_records_inbound_to_memory() -> None:
    from opencs.memory.memory_store import MemoryStore

    registry = ChannelRegistry()
    registry.register(WebChatAdapter())

    mem = MemoryStore()
    llm = FakeLLMClient(responses=["ok"])
    worker = CSReplyWorker(llm=llm, model="fake")
    guard = _guard()

    orch = Orchestrator(workers=[worker], guard=guard, registry=registry, memory_store=mem)
    await orch.handle(message=_inbound("hi"))

    rows = mem.l0.list(conversation_id="conv-1")
    assert len(rows) == 1
    assert rows[0].kind == "inbound_message"


async def test_orchestrator_injects_l2_summary_into_worker_context() -> None:
    from opencs.memory.memory_store import MemoryStore

    registry = ChannelRegistry()
    registry.register(WebChatAdapter())

    mem = MemoryStore()
    mem.write_l2(
        subject_id="customer:cust-1",
        kind="customer_profile",
        body="VIP customer, prefers quick responses.",
    )

    received_contexts: list[dict] = []

    class _CapturingWorker(CSReplyWorker):
        async def run(self, inp: WorkerInput) -> list[ActionPlan]:
            received_contexts.append(dict(inp.session_context))
            return await super().run(inp)

    llm = FakeLLMClient(responses=["ok"])
    worker = _CapturingWorker(llm=llm, model="fake")
    guard = _guard()

    orch = Orchestrator(workers=[worker], guard=guard, registry=registry, memory_store=mem)
    await orch.handle(message=_inbound("hello"))

    assert len(received_contexts) == 1
    assert "VIP" in (received_contexts[0].get("l2_summary") or "")


async def test_orchestrator_injects_skill_matches_into_worker_context() -> None:
    import tempfile
    from pathlib import Path

    from opencs.skills.skill_repo import SkillRepo

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "refund"
        skill_dir.mkdir()
        skill_content = (
            "---\nname: refund\ndescription: Refund policy\n"
            "keywords:\n  - refund\n---\nHandle refunds carefully.\n"
        )
        (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")

        registry = ChannelRegistry()
        registry.register(WebChatAdapter())

        received_contexts: list[dict] = []

        class _CapturingWorker(CSReplyWorker):
            async def run(self, inp: WorkerInput) -> list[ActionPlan]:
                received_contexts.append(dict(inp.session_context))
                return await super().run(inp)

        llm = FakeLLMClient(responses=["ok"])
        worker = _CapturingWorker(llm=llm, model="fake")
        guard = _guard()
        repo = SkillRepo(skills_dir=tmpdir)

        orch = Orchestrator(
            workers=[worker], guard=guard, registry=registry, skill_repo=repo
        )
        await orch.handle(message=_inbound("I want a refund"))

        assert received_contexts[0].get("skills") == ["Handle refunds carefully."]


def test_orchestrator_handle_is_observable(monkeypatch) -> None:
    """Sanity check: Orchestrator.handle is wrapped by a Langfuse observe decorator."""
    from opencs.agents.orchestrator import Orchestrator
    assert getattr(Orchestrator.handle, "__langfuse_observed__", False) is True
