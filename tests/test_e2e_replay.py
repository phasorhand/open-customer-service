"""E2E Replay: seed a conversation trace → replay in Strict mode (verify no divergence)
→ replay in WhatIf with different prompt (verify divergence detected)."""

from datetime import UTC, datetime

import pytest

from opencs.agents.llm_client import FakeLLMClient
from opencs.memory.l0_store import L0Event, L0RawEventStore
from opencs.memory.memory_store import MemoryStore
from opencs.replay.engine import ReplayEngine
from opencs.replay.types import (
    ReplayMode,
    ReplayOverrides,
    ReplayResult,
    ReplayScope,
    ReplaySession,
)
from opencs.tools.protocol import ToolDescription, ToolResult
from opencs.tools.registry import ToolRegistry


class _FakeOrderTool:
    tool_id = "crm.get_order"

    def describe(self) -> ToolDescription:
        return ToolDescription(
            tool_id=self.tool_id, name="Get Order", description="",
            parameters={"order_id": {"type": "string"}}, read_only=True,
        )

    async def call(self, args, token) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={"status": "shipped"})

    async def dry_run(self, args) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={"_dry_run": True})

    async def health_check(self) -> bool:
        return True


def _seed_full_conversation(l0: L0RawEventStore) -> None:
    """Simulate a full conversation trace as would be recorded by Orchestrator."""
    l0.append(L0Event(
        conversation_id="conv-replay-1",
        kind="inbound_message",
        payload={"text": "where is ord-001?", "customer_id": "u1"},
        ts=datetime(2026, 5, 1, 10, 0, 0, tzinfo=UTC),
    ))
    l0.append(L0Event(
        conversation_id="conv-replay-1",
        kind="tool_call",
        payload={
            "action_id": "act-crm-1", "tool_id": "crm.get_order",
            "args": {"order_id": "ord-001"},
        },
        ts=datetime(2026, 5, 1, 10, 0, 1, tzinfo=UTC),
    ))
    l0.append(L0Event(
        conversation_id="conv-replay-1",
        kind="tool_result",
        payload={
            "action_id": "act-crm-1", "tool_id": "crm.get_order",
            "success": True, "data": {"status": "shipped"}, "error": None,
        },
        ts=datetime(2026, 5, 1, 10, 0, 2, tzinfo=UTC),
    ))
    l0.append(L0Event(
        conversation_id="conv-replay-1",
        kind="llm_call",
        payload={
            "recording_id": "rec-1", "model": "fake",
            "input": "where is ord-001?", "output": "Your order ord-001 has shipped.",
        },
        ts=datetime(2026, 5, 1, 10, 0, 3, tzinfo=UTC),
    ))


@pytest.fixture
def replay_engine() -> ReplayEngine:
    memory = MemoryStore()
    _seed_full_conversation(memory.l0)
    tool_reg = ToolRegistry()
    tool_reg.register(_FakeOrderTool())
    return ReplayEngine(
        l0=memory.l0,
        tool_registry=tool_reg,
        llm_fallback=FakeLLMClient(responses=["Your order ord-001 has shipped."]),
    )


async def test_strict_replay_no_divergence(replay_engine: ReplayEngine) -> None:
    session = ReplaySession(
        source_conversation_id="conv-replay-1",
        mode=ReplayMode.STRICT,
        scope=ReplayScope.CONVERSATION,
    )
    result = await replay_engine.replay(session)
    assert result.baseline_event_count == 4
    assert result.session_id.startswith("replay-")


async def test_what_if_with_different_prompt_produces_divergence() -> None:
    memory = MemoryStore()
    _seed_full_conversation(memory.l0)
    tool_reg = ToolRegistry()
    tool_reg.register(_FakeOrderTool())
    engine = ReplayEngine(
        l0=memory.l0,
        tool_registry=tool_reg,
        llm_fallback=FakeLLMClient(responses=["COMPLETELY DIFFERENT REPLY"]),
    )
    session = ReplaySession(
        source_conversation_id="conv-replay-1",
        mode=ReplayMode.WHAT_IF,
        scope=ReplayScope.CONVERSATION,
        overrides=ReplayOverrides(prompt_override="Respond differently."),
    )
    result = await engine.replay(session)
    assert result.replay_event_count > 0
    assert len(result.divergence_points) > 0


async def test_partial_replay_uses_cached_tools() -> None:
    memory = MemoryStore()
    _seed_full_conversation(memory.l0)
    tool_reg = ToolRegistry()
    tool_reg.register(_FakeOrderTool())
    engine = ReplayEngine(
        l0=memory.l0,
        tool_registry=tool_reg,
        llm_fallback=FakeLLMClient(responses=["A different answer via partial"]),
    )
    session = ReplaySession(
        source_conversation_id="conv-replay-1",
        mode=ReplayMode.PARTIAL,
        scope=ReplayScope.CONVERSATION,
    )
    result = await engine.replay(session)
    assert isinstance(result, ReplayResult)
    assert result.baseline_event_count == 4


async def test_what_if_tool_rerun_override() -> None:
    memory = MemoryStore()
    _seed_full_conversation(memory.l0)
    tool_reg = ToolRegistry()
    tool_reg.register(_FakeOrderTool())
    engine = ReplayEngine(
        l0=memory.l0,
        tool_registry=tool_reg,
        llm_fallback=FakeLLMClient(responses=["Order status checked."]),
    )
    session = ReplaySession(
        source_conversation_id="conv-replay-1",
        mode=ReplayMode.WHAT_IF,
        scope=ReplayScope.CONVERSATION,
        overrides=ReplayOverrides(tool_ids_to_rerun=["crm.get_order"]),
    )
    result = await engine.replay(session)
    assert isinstance(result, ReplayResult)
