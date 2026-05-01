from datetime import UTC, datetime

import pytest

from opencs.memory.l0_store import L0Event, L0RawEventStore


def test_append_and_list_back(tmp_path) -> None:
    store = L0RawEventStore(db_path=str(tmp_path / "l0.db"))
    evt = L0Event(
        conversation_id="conv-1",
        kind="inbound_message",
        payload={"text": "hello"},
        ts=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
    )
    store.append(evt)
    rows = store.list(conversation_id="conv-1")
    assert len(rows) == 1
    assert rows[0].kind == "inbound_message"
    assert rows[0].payload["text"] == "hello"


def test_multiple_events_ordered_by_ts(tmp_path) -> None:
    store = L0RawEventStore(db_path=str(tmp_path / "l0.db"))
    for i in range(3):
        store.append(L0Event(
            conversation_id="conv-1",
            kind="action_guard_decision",
            payload={"action_id": f"act-{i}"},
            ts=datetime(2026, 5, 1, i + 1, tzinfo=UTC),
        ))
    rows = store.list(conversation_id="conv-1")
    assert [r.payload["action_id"] for r in rows] == ["act-0", "act-1", "act-2"]


def test_list_isolates_by_conversation(tmp_path) -> None:
    store = L0RawEventStore(db_path=str(tmp_path / "l0.db"))
    store.append(L0Event(
        conversation_id="conv-A",
        kind="inbound_message",
        payload={"text": "for A"},
        ts=datetime(2026, 5, 1, tzinfo=UTC),
    ))
    store.append(L0Event(
        conversation_id="conv-B",
        kind="inbound_message",
        payload={"text": "for B"},
        ts=datetime(2026, 5, 1, tzinfo=UTC),
    ))
    assert len(store.list(conversation_id="conv-A")) == 1
    assert len(store.list(conversation_id="conv-B")) == 1


def test_in_memory_db() -> None:
    store = L0RawEventStore(db_path=":memory:")
    store.append(L0Event(
        conversation_id="c",
        kind="test",
        payload={},
        ts=datetime(2026, 5, 1, tzinfo=UTC),
    ))
    assert len(store.list(conversation_id="c")) == 1
