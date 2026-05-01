from opencs.memory.l2_store import L2MemoryStore, MemoryEntry


def test_write_and_read_back(tmp_path) -> None:
    store = L2MemoryStore(db_path=str(tmp_path / "l2.db"))
    store.write(MemoryEntry(
        subject_id="customer:u1",
        kind="customer_profile",
        body="Customer prefers email contact. VIP tier.",
    ))
    entries = store.search("VIP", limit=5)
    assert len(entries) == 1
    assert "VIP" in entries[0].body


def test_search_returns_empty_when_no_match(tmp_path) -> None:
    store = L2MemoryStore(db_path=str(tmp_path / "l2.db"))
    store.write(MemoryEntry(
        subject_id="customer:u1",
        kind="customer_profile",
        body="Customer likes product A.",
    ))
    assert store.search("nonexistent-keyword-xyz", limit=5) == []


def test_get_by_subject(tmp_path) -> None:
    store = L2MemoryStore(db_path=str(tmp_path / "l2.db"))
    store.write(MemoryEntry(
        subject_id="customer:u2",
        kind="customer_profile",
        body="Prefers phone contact.",
    ))
    entries = store.get_by_subject("customer:u2")
    assert len(entries) == 1
    assert entries[0].subject_id == "customer:u2"


def test_multiple_writes_to_same_subject_are_all_kept(tmp_path) -> None:
    store = L2MemoryStore(db_path=str(tmp_path / "l2.db"))
    store.write(MemoryEntry(subject_id="c:u1", kind="note", body="First note"))
    store.write(MemoryEntry(subject_id="c:u1", kind="note", body="Second note"))
    entries = store.get_by_subject("c:u1")
    assert len(entries) == 2


def test_search_multiple_results(tmp_path) -> None:
    store = L2MemoryStore(db_path=str(tmp_path / "l2.db"))
    store.write(MemoryEntry(subject_id="c:u1", kind="note", body="refund requested"))
    store.write(MemoryEntry(subject_id="c:u2", kind="note", body="refund processed"))
    store.write(MemoryEntry(subject_id="c:u3", kind="note", body="shipping delay"))
    results = store.search("refund", limit=10)
    assert len(results) == 2
