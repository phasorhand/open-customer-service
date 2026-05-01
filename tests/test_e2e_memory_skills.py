import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from opencs.agents.base_worker import WorkerInput
from opencs.agents.cs_reply import CSReplyWorker
from opencs.agents.llm_client import FakeLLMClient
from opencs.agents.orchestrator import Orchestrator
from opencs.channel.registry import ChannelRegistry
from opencs.channel.webchat import WebChatAdapter
from opencs.gateway.app import create_app
from opencs.harness.action_guard import ActionGuard
from opencs.harness.action_plan import ActionPlan, RiskTier
from opencs.harness.audit_log import AuditLog
from opencs.harness.hitl_queue import HITLQueue
from opencs.harness.token import TokenFactory
from opencs.memory.memory_store import MemoryStore
from opencs.skills.skill_repo import SkillRepo


class _GreenCSWorker(CSReplyWorker):
    async def run(self, inp: WorkerInput) -> list[ActionPlan]:
        plans = await super().run(inp)
        return [
            ActionPlan(
                action_id=p.action_id,
                tool_id=p.tool_id,
                args=p.args,
                intent=p.intent,
                risk_hint=RiskTier.GREEN,
            )
            for p in plans
        ]


def test_e2e_skill_injected_into_prompt_and_memory_records_event() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "refund"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: refund\ndescription: Refund policy\nkeywords:\n  - refund\n---\n"
            "Always ask for order number before processing refunds.\n",
            encoding="utf-8",
        )

        registry = ChannelRegistry()
        webchat = WebChatAdapter()
        registry.register(webchat)

        guard = ActionGuard(
            token_factory=TokenFactory(secret_key=b"e2e-secret", default_ttl_seconds=60),
            audit_log=AuditLog(db_path=":memory:"),
            hitl_queue=HITLQueue(),
        )
        mem = MemoryStore()
        repo = SkillRepo(skills_dir=tmpdir)
        llm = FakeLLMClient(responses=["Please provide your order number."])
        worker = _GreenCSWorker(llm=llm, model="fake")
        orch = Orchestrator(
            workers=[worker],
            guard=guard,
            registry=registry,
            memory_store=mem,
            skill_repo=repo,
        )

        async def _handler(msg):
            await orch.handle(message=msg)

        app = create_app(registry, webchat_handler=_handler)
        client = TestClient(app)

        with client.websocket_connect("/ws/webchat?conversation_id=conv-e2e&customer_id=u1") as ws:
            ws.send_json({"text": "I want a refund", "ts_iso": "2026-05-01T00:00:00+00:00"})
            reply = ws.receive_json()
            assert reply["kind"] == "reply"
            assert "order number" in reply["content"][0]["text"].lower()

        rows = mem.l0.list(conversation_id="conv-e2e")
        assert len(rows) == 1
        assert rows[0].kind == "inbound_message"

        system_msg = next(m for m in llm.calls[-1]["messages"] if m.role == "system")
        assert "order number" in system_msg.content.lower()
