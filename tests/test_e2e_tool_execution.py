"""E2E: customer mentions an order → CSReplyWorker emits crm.get_order plan →
ActionGuard auto-approves (GREEN) → ToolExecutor calls mock CRM → L0 has
tool_call + tool_result events."""

from datetime import UTC, datetime

import httpx
import pytest
from fastapi import FastAPI

from opencs.agents.cs_reply import CSReplyWorker
from opencs.agents.llm_client import FakeLLMClient
from opencs.agents.orchestrator import Orchestrator
from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import ContentPart, InboundMessage
from opencs.channel.webchat import WebChatAdapter
from opencs.harness.action_guard import ActionGuard
from opencs.harness.audit_log import AuditLog
from opencs.harness.hitl_queue import HITLQueue
from opencs.harness.token import TokenFactory
from opencs.memory.memory_store import MemoryStore
from opencs.tools.api_tool import APITool
from opencs.tools.executor import ToolExecutor
from opencs.tools.mock_crm import router as crm_router
from opencs.tools.registry import ToolRegistry

_SECRET = b"e2e-secret"


@pytest.fixture
def crm_transport() -> httpx.ASGITransport:
    app = FastAPI()
    app.include_router(crm_router)
    return httpx.ASGITransport(app=app)


@pytest.fixture
def full_stack(crm_transport: httpx.ASGITransport) -> tuple[Orchestrator, MemoryStore]:
    channel_registry = ChannelRegistry()
    channel_registry.register(WebChatAdapter())

    tool_registry = ToolRegistry()
    tool_registry.register(APITool(
        tool_id="crm.get_order",
        base_url="http://test",
        method="GET",
        path_template="/mock-crm/orders/{order_id}",
        parameters_schema={"order_id": {"type": "string"}},
        read_only=True,
        _transport=crm_transport,
    ))
    tool_executor = ToolExecutor(registry=tool_registry)

    memory = MemoryStore()
    guard = ActionGuard(
        token_factory=TokenFactory(secret_key=_SECRET),
        audit_log=AuditLog(),
        hitl_queue=HITLQueue(),
    )
    llm = FakeLLMClient(responses=["Let me check your order status."] * 10)
    worker = CSReplyWorker(llm=llm, model="fake")
    orch = Orchestrator(
        workers=[worker],
        guard=guard,
        registry=channel_registry,
        memory_store=memory,
        tool_executor=tool_executor,
    )
    return orch, memory


def _msg(text: str, conv_id: str = "conv-1") -> InboundMessage:
    return InboundMessage(
        channel_id="webchat",
        conversation_id=conv_id,
        customer_id="u1",
        sender_kind="customer",
        content=[ContentPart(kind="text", text=text)],
        timestamp=datetime(2026, 5, 1, tzinfo=UTC),
        raw_payload={},
        platform_meta={},
    )


async def test_order_query_produces_tool_call_and_result_in_l0(
    full_stack: tuple[Orchestrator, MemoryStore],
) -> None:
    orch, memory = full_stack
    await orch.handle(message=_msg("where is my package for ord-001?"))

    events = memory.l0.list(conversation_id="conv-1")
    kinds = [e.kind for e in events]

    assert "tool_call" in kinds
    assert "tool_result" in kinds

    tool_call = next(e for e in events if e.kind == "tool_call")
    assert tool_call.payload["tool_id"] == "crm.get_order"
    assert tool_call.payload["args"]["order_id"] == "ord-001"

    tool_result = next(e for e in events if e.kind == "tool_result")
    assert tool_result.payload["success"] is True
    assert tool_result.payload["data"]["status"] == "shipped"


async def test_message_without_order_has_no_tool_events(
    full_stack: tuple[Orchestrator, MemoryStore],
) -> None:
    orch, memory = full_stack
    await orch.handle(message=_msg("hello, how are you?", conv_id="conv-2"))

    events = memory.l0.list(conversation_id="conv-2")
    tool_kinds = {e.kind for e in events} & {"tool_call", "tool_result"}
    assert tool_kinds == set()


async def test_unknown_order_id_produces_failed_tool_result(
    full_stack: tuple[Orchestrator, MemoryStore],
) -> None:
    orch, memory = full_stack
    await orch.handle(message=_msg("check ord-999 please", conv_id="conv-3"))

    events = memory.l0.list(conversation_id="conv-3")
    tool_result = next((e for e in events if e.kind == "tool_result"), None)
    assert tool_result is not None
    assert tool_result.payload["success"] is False
    assert tool_result.payload["error"] is not None
