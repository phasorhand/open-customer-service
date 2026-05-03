from datetime import UTC, datetime

import pytest

from opencs.agents.base_worker import BaseWorker, WorkerInput
from opencs.agents.orchestrator import Orchestrator
from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import ContentPart, InboundMessage
from opencs.channel.webchat import WebChatAdapter
from opencs.harness.action_guard import ActionGuard
from opencs.harness.action_plan import ActionPlan, RiskTier
from opencs.harness.audit_log import AuditLog
from opencs.harness.hitl_queue import HITLQueue
from opencs.harness.token import TokenFactory
from opencs.memory.memory_store import MemoryStore
from opencs.tools.executor import ToolExecutor
from opencs.tools.protocol import ToolDescription, ToolResult
from opencs.tools.registry import ToolRegistry

_SECRET = b"test-secret"


class _FakeCRMTool:
    tool_id = "crm.get_order"

    def describe(self) -> ToolDescription:
        return ToolDescription(
            tool_id=self.tool_id, name="Get Order", description="test",
            parameters={"order_id": {"type": "string"}}, read_only=True,
        )

    async def call(self, args, token) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={"status": "shipped"})

    async def dry_run(self, args) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={"_dry_run": True})

    async def health_check(self) -> bool:
        return True


class _CRMLookupWorker(BaseWorker):
    worker_id = "crm_lookup"

    async def run(self, inp: WorkerInput) -> list[ActionPlan]:
        return [ActionPlan(
            action_id="act-crm-1",
            tool_id="crm.get_order",
            args={"order_id": "ord-001"},
            intent="look up order",
            risk_hint=RiskTier.GREEN,
        )]


def _msg(text: str = "what is the status of ord-001?") -> InboundMessage:
    return InboundMessage(
        channel_id="webchat",
        conversation_id="conv-1",
        customer_id="u1",
        sender_kind="customer",
        content=[ContentPart(kind="text", text=text)],
        timestamp=datetime(2026, 5, 1, tzinfo=UTC),
        raw_payload={},
        platform_meta={},
    )


@pytest.fixture
def orch_with_tool() -> tuple[Orchestrator, MemoryStore]:
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    tool_registry = ToolRegistry()
    tool_registry.register(_FakeCRMTool())
    tool_executor = ToolExecutor(registry=tool_registry)
    memory = MemoryStore()
    guard = ActionGuard(
        token_factory=TokenFactory(secret_key=_SECRET),
        audit_log=AuditLog(),
        hitl_queue=HITLQueue(),
    )
    orch = Orchestrator(
        workers=[_CRMLookupWorker()],
        guard=guard,
        registry=registry,
        memory_store=memory,
        tool_executor=tool_executor,
    )
    return orch, memory


async def test_orchestrator_dispatches_tool_plan(
    orch_with_tool: tuple[Orchestrator, MemoryStore],
) -> None:
    orch, memory = orch_with_tool
    await orch.handle(message=_msg())
    events = memory.l0.list(conversation_id="conv-1")
    tool_call_events = [e for e in events if e.kind == "tool_call"]
    tool_result_events = [e for e in events if e.kind == "tool_result"]
    assert len(tool_call_events) == 1
    assert tool_call_events[0].payload["tool_id"] == "crm.get_order"
    assert len(tool_result_events) == 1
    assert tool_result_events[0].payload["success"] is True


async def test_orchestrator_without_tool_executor_ignores_non_channel_plans() -> None:
    """Without tool_executor, non-channel.send plans are silently skipped."""
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    guard = ActionGuard(
        token_factory=TokenFactory(secret_key=_SECRET),
        audit_log=AuditLog(),
        hitl_queue=HITLQueue(),
    )
    orch = Orchestrator(
        workers=[_CRMLookupWorker()],
        guard=guard,
        registry=registry,
    )
    # Should not raise
    await orch.handle(message=_msg())
