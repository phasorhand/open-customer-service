from datetime import UTC, datetime

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


class _GreenCSWorker(CSReplyWorker):
    """CSReplyWorker override that uses GREEN tier so ActionGuard auto-approves."""

    async def run(self, inp: WorkerInput) -> list[ActionPlan]:
        plans = await super().run(inp)
        green_plans = []
        for p in plans:
            green_plans.append(ActionPlan(
                action_id=p.action_id,
                tool_id=p.tool_id,
                args=p.args,
                intent=p.intent,
                risk_hint=RiskTier.GREEN,
            ))
        return green_plans


def test_e2e_webchat_ws_reply() -> None:
    registry = ChannelRegistry()
    webchat = WebChatAdapter()
    registry.register(webchat)

    guard = ActionGuard(
        token_factory=TokenFactory(secret_key=b"e2e-secret", default_ttl_seconds=60),
        audit_log=AuditLog(db_path=":memory:"),
        hitl_queue=HITLQueue(),
    )
    llm = FakeLLMClient(responses=["Hello from e2e!"])
    worker = _GreenCSWorker(llm=llm, model="fake")
    orch = Orchestrator(workers=[worker], guard=guard, registry=registry)

    async def _handler(msg):
        await orch.handle(message=msg)

    app = create_app(registry, webchat_handler=_handler)
    client = TestClient(app)

    with client.websocket_connect("/ws/webchat?conversation_id=conv-e2e&customer_id=u1") as ws:
        ws.send_json({"text": "hi bot", "ts_iso": "2026-05-01T00:00:00+00:00"})
        reply = ws.receive_json()
        assert reply["kind"] == "reply"
        assert reply["content"][0]["text"] == "Hello from e2e!"

    # Audit log has one auto_approved entry
    entries = guard._log.recent(limit=5)
    assert any(e.decision == "auto_approved" for e in entries)
