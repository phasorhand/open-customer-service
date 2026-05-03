import uuid
from datetime import UTC, datetime

import pytest

from opencs.agents.llm_client import FakeLLMClient, LLMMessage
from opencs.memory.l0_store import L0Event, L0RawEventStore
from opencs.memory.memory_store import MemoryStore
from opencs.replay.engine import ReplayEngine
from opencs.replay.types import ReplayMode, ReplayOverrides, ReplayResult, ReplayScope, ReplaySession, Verdict
from opencs.tools.protocol import ToolDescription, ToolResult
from opencs.tools.registry import ToolRegistry


class _FakeTool:
    def __init__(self, tool_id: str = "crm.get_order") -> None:
        self.tool_id = tool_id

    def describe(self) -> ToolDescription:
        return ToolDescription(tool_id=self.tool_id, name=self.tool_id, description="", parameters={}, read_only=True)

    async def call(self, args, token) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={"status": "live_call"})

    async def dry_run(self, args) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={"_dry_run": True})

    async def health_check(self) -> bool:
        return True


def _seed_trace(l0: L0RawEventStore, conv_id: str = "conv-1") -> None:
    """Seed a minimal trace: inbound → llm_call → channel.send captured."""
    l0.append(L0Event(
        conversation_id=conv_id,
        kind="inbound_message",
        payload={"text": "hello", "customer_id": "u1"},
        ts=datetime(2026, 5, 1, 10, 0, 0, tzinfo=UTC),
    ))
    l0.append(L0Event(
        conversation_id=conv_id,
        kind="llm_call",
        payload={"recording_id": "rec-1", "model": "fake", "input": "hello", "output": "Hi there!"},
        ts=datetime(2026, 5, 1, 10, 0, 1, tzinfo=UTC),
    ))


@pytest.fixture
def memory() -> MemoryStore:
    return MemoryStore()


@pytest.fixture
def seeded_memory() -> MemoryStore:
    m = MemoryStore()
    _seed_trace(m.l0, "conv-1")
    return m


@pytest.fixture
def tool_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(_FakeTool())
    return reg


async def test_strict_replay_produces_result(seeded_memory: MemoryStore, tool_registry: ToolRegistry) -> None:
    engine = ReplayEngine(
        l0=seeded_memory.l0,
        tool_registry=tool_registry,
        llm_fallback=FakeLLMClient(responses=["fallback"]),
    )
    session = ReplaySession(
        source_conversation_id="conv-1",
        mode=ReplayMode.STRICT,
        scope=ReplayScope.CONVERSATION,
    )
    result = await engine.replay(session)
    assert isinstance(result, ReplayResult)
    assert result.session_id != ""
    assert result.baseline_event_count == 2


async def test_strict_replay_uses_cached_llm(seeded_memory: MemoryStore, tool_registry: ToolRegistry) -> None:
    fallback = FakeLLMClient(responses=["SHOULD NOT BE CALLED"])
    engine = ReplayEngine(
        l0=seeded_memory.l0,
        tool_registry=tool_registry,
        llm_fallback=fallback,
    )
    session = ReplaySession(
        source_conversation_id="conv-1",
        mode=ReplayMode.STRICT,
        scope=ReplayScope.CONVERSATION,
    )
    result = await engine.replay(session)
    assert len(fallback.calls) == 0


async def test_what_if_with_prompt_override(seeded_memory: MemoryStore, tool_registry: ToolRegistry) -> None:
    fallback = FakeLLMClient(responses=["I am strict now."])
    engine = ReplayEngine(
        l0=seeded_memory.l0,
        tool_registry=tool_registry,
        llm_fallback=fallback,
    )
    session = ReplaySession(
        source_conversation_id="conv-1",
        mode=ReplayMode.WHAT_IF,
        scope=ReplayScope.CONVERSATION,
        overrides=ReplayOverrides(prompt_override="Be very strict."),
    )
    result = await engine.replay(session)
    assert result.verdict in (Verdict.BADCASE_FIXED, Verdict.INCONCLUSIVE, Verdict.BADCASE_REMAINS, Verdict.NEW_REGRESSION)
    assert len(fallback.calls) >= 1


async def test_empty_conversation_returns_inconclusive(memory: MemoryStore, tool_registry: ToolRegistry) -> None:
    engine = ReplayEngine(
        l0=memory.l0,
        tool_registry=tool_registry,
        llm_fallback=FakeLLMClient(responses=["x"]),
    )
    session = ReplaySession(
        source_conversation_id="conv-nonexistent",
        mode=ReplayMode.STRICT,
        scope=ReplayScope.CONVERSATION,
    )
    result = await engine.replay(session)
    assert result.verdict == Verdict.INCONCLUSIVE
    assert result.baseline_event_count == 0
