from datetime import UTC, datetime

from opencs.channel.schema import ContentPart, InboundMessage
from opencs.memory.memory_store import MemoryStore


def _msg(text: str = "hello", conv_id: str = "conv-1", customer_id: str = "u1") -> InboundMessage:
    return InboundMessage(
        channel_id="webchat",
        conversation_id=conv_id,
        customer_id=customer_id,
        sender_kind="customer",
        content=[ContentPart(kind="text", text=text)],
        timestamp=datetime(2026, 5, 1, tzinfo=UTC),
        raw_payload={},
        platform_meta={},
    )


def test_record_inbound_writes_l0() -> None:
    store = MemoryStore()
    msg = _msg()
    store.record_inbound(msg)
    rows = store.l0.list(conversation_id="conv-1")
    assert len(rows) == 1
    assert rows[0].kind == "inbound_message"
    assert rows[0].payload["text"] == "hello"


def test_load_context_increments_turn_count() -> None:
    store = MemoryStore()
    msg = _msg()
    store.record_inbound(msg)
    ctx = store.load_context(
        conversation_id="conv-1",
        customer_id="u1",
        message_text="hello",
    )
    assert ctx["turn_count"] == 1
    store.record_inbound(msg)
    ctx2 = store.load_context("conv-1", customer_id="u1", message_text="hello")
    assert ctx2["turn_count"] == 2


def test_load_context_includes_l2_summary_when_matching() -> None:
    store = MemoryStore()
    from opencs.memory.l2_store import MemoryEntry
    store.l2.write(MemoryEntry(
        subject_id="customer:u1",
        kind="customer_profile",
        body="Customer prefers email. VIP tier.",
    ))
    ctx = store.load_context(
        conversation_id="conv-1",
        customer_id="u1",
        message_text="contact me",
    )
    assert ctx["l2_summary"] is not None
    assert "VIP" in ctx["l2_summary"]


def test_load_context_l2_summary_none_when_no_match() -> None:
    store = MemoryStore()
    ctx = store.load_context(
        conversation_id="conv-new",
        customer_id="u-new",
        message_text="hello",
    )
    assert ctx["l2_summary"] is None


def test_write_l2_stores_entry() -> None:
    store = MemoryStore()
    store.write_l2(
        subject_id="customer:u1",
        kind="customer_profile",
        body="Likes product B.",
    )
    entries = store.l2.get_by_subject("customer:u1")
    assert len(entries) == 1
    assert "product B" in entries[0].body


def test_write_l2_invokes_evolution_hook_when_configured() -> None:
    hook_calls: list[tuple[str, str, str]] = []

    def evolution_hook(*, subject_id: str, kind: str, body: str) -> None:
        hook_calls.append((subject_id, kind, body))

    store = MemoryStore(l0_db=":memory:", l2_db=":memory:", evolution_hook=evolution_hook)
    store.write_l2(subject_id="customer:c1", kind="preference", body="likes blue")
    assert hook_calls == [("customer:c1", "preference", "likes blue")]


def test_write_l2_without_hook_still_writes() -> None:
    store = MemoryStore(l0_db=":memory:", l2_db=":memory:")
    version_id = store.write_l2(subject_id="customer:c1", kind="preference", body="likes red")
    assert version_id  # Non-empty string means write succeeded
