from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from opencs.tracing.langfuse_client import (
    LangfuseClient,
    get_current_trace_id,
    init_langfuse,
)


def test_init_langfuse_disabled_when_no_keys(monkeypatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    client = init_langfuse()
    assert client.enabled is False


def test_init_langfuse_enabled_with_keys(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_HOST", "http://langfuse:3001")
    with patch("opencs.tracing.langfuse_client.Langfuse") as fake:
        fake.return_value = MagicMock()
        client = init_langfuse()
    assert client.enabled is True


def test_get_current_trace_id_returns_none_when_disabled() -> None:
    client = LangfuseClient(sdk=None)
    assert client.get_current_trace_id() is None


def test_get_current_trace_id_reads_from_sdk() -> None:
    fake_sdk = MagicMock()
    fake_sdk.get_current_trace_id.return_value = "trace-xyz"
    client = LangfuseClient(sdk=fake_sdk)
    assert client.get_current_trace_id() == "trace-xyz"
