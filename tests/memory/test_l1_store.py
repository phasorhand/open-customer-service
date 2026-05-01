from opencs.memory.l1_store import L1SessionStore


def test_set_and_get_field() -> None:
    store = L1SessionStore()
    store.set("conv-1", "turn_count", 3)
    assert store.get("conv-1", "turn_count") == 3


def test_get_missing_key_returns_none() -> None:
    store = L1SessionStore()
    assert store.get("conv-1", "missing") is None


def test_get_missing_conversation_returns_none() -> None:
    store = L1SessionStore()
    assert store.get("no-such-conv", "key") is None


def test_get_all_returns_copy() -> None:
    store = L1SessionStore()
    store.set("c", "k", "v")
    snapshot = store.get_all("c")
    snapshot["k"] = "mutated"
    assert store.get("c", "k") == "v"  # original unchanged


def test_close_removes_session() -> None:
    store = L1SessionStore()
    store.set("c", "k", "v")
    store.close("c")
    assert store.get("c", "k") is None


def test_increment_turn_count() -> None:
    store = L1SessionStore()
    store.set("c", "turn_count", 0)
    store.set("c", "turn_count", store.get("c", "turn_count") + 1)
    assert store.get("c", "turn_count") == 1
