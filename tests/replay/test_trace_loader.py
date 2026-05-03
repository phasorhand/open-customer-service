from datetime import UTC, datetime

import pytest

from opencs.memory.l0_store import L0Event, L0RawEventStore
from opencs.replay.trace_loader import TraceLoader


@pytest.fixture
def l0() -> L0RawEventStore:
    store = L0RawEventStore()
    store.append(L0Event(
        conversation_id="conv-1",
        kind="inbound_message",
        payload={"text": "where is ord-001?", "customer_id": "u1"},
        ts=datetime(2026, 5, 1, 10, 0, 0, tzinfo=UTC),
    ))
    store.append(L0Event(
        conversation_id="conv-1",
        kind="tool_call",
        payload={"action_id": "act-1", "tool_id": "crm.get_order", "args": {"order_id": "ord-001"}},
        ts=datetime(2026, 5, 1, 10, 0, 1, tzinfo=UTC),
    ))
    store.append(L0Event(
        conversation_id="conv-1",
        kind="tool_result",
        payload={"action_id": "act-1", "tool_id": "crm.get_order", "success": True,
                 "data": {"status": "shipped"}, "error": None},
        ts=datetime(2026, 5, 1, 10, 0, 2, tzinfo=UTC),
    ))
    store.append(L0Event(
        conversation_id="conv-1",
        kind="llm_call",
        payload={"recording_id": "rec-1", "model": "fake", "input": "where is ord-001?",
                 "output": "Your order has shipped."},
        ts=datetime(2026, 5, 1, 10, 0, 3, tzinfo=UTC),
    ))
    return store


def test_load_trace_returns_all_events(l0: L0RawEventStore) -> None:
    loader = TraceLoader(l0=l0)
    trace = loader.load("conv-1")
    assert len(trace.events) == 4
    assert trace.conversation_id == "conv-1"


def test_load_trace_extracts_inbound_messages(l0: L0RawEventStore) -> None:
    loader = TraceLoader(l0=l0)
    trace = loader.load("conv-1")
    assert len(trace.inbound_messages) == 1
    assert trace.inbound_messages[0].payload["text"] == "where is ord-001?"


def test_load_trace_extracts_llm_cache(l0: L0RawEventStore) -> None:
    loader = TraceLoader(l0=l0)
    trace = loader.load("conv-1")
    assert "rec-1" in trace.llm_cache
    assert trace.llm_cache["rec-1"] == "Your order has shipped."


def test_load_trace_extracts_tool_cache(l0: L0RawEventStore) -> None:
    loader = TraceLoader(l0=l0)
    trace = loader.load("conv-1")
    assert "act-1" in trace.tool_cache
    assert trace.tool_cache["act-1"]["success"] is True
    assert trace.tool_cache["act-1"]["data"]["status"] == "shipped"


def test_load_nonexistent_conversation(l0: L0RawEventStore) -> None:
    loader = TraceLoader(l0=l0)
    trace = loader.load("conv-999")
    assert len(trace.events) == 0
    assert trace.inbound_messages == []


def test_l0_list_by_kinds(l0: L0RawEventStore) -> None:
    events = l0.list_by_kinds(conversation_id="conv-1", kinds=["tool_call", "tool_result"])
    assert len(events) == 2
    assert all(e.kind in ("tool_call", "tool_result") for e in events)
