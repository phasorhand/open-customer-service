from __future__ import annotations

from opencs.evolution.crm_config_store import CRMConfig, CRMConfigStore


def test_save_and_get_config() -> None:
    store = CRMConfigStore(db_path=":memory:")
    cfg = CRMConfig(
        base_url="https://crm.example.com",
        schema_json='{"openapi":"3.0"}',
        exposed_operations=["getCustomer", "createTicket"],
    )
    store.save(cfg)
    loaded = store.get()
    assert loaded is not None
    assert loaded.base_url == "https://crm.example.com"
    assert loaded.exposed_operations == ["getCustomer", "createTicket"]


def test_get_returns_none_when_empty() -> None:
    store = CRMConfigStore(db_path=":memory:")
    assert store.get() is None


def test_save_overwrites_previous() -> None:
    store = CRMConfigStore(db_path=":memory:")
    store.save(CRMConfig(base_url="https://v1.example.com", schema_json="{}", exposed_operations=[]))
    store.save(CRMConfig(base_url="https://v2.example.com", schema_json="{}", exposed_operations=["a"]))
    loaded = store.get()
    assert loaded is not None
    assert loaded.base_url == "https://v2.example.com"
    assert loaded.exposed_operations == ["a"]
