from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

try:
    from langfuse import Langfuse
except ImportError:  # pragma: no cover
    Langfuse = None


@dataclass
class LangfuseClient:
    """Thin wrapper around the Langfuse SDK. When disabled (no keys), all ops no-op."""

    sdk: Any | None

    @property
    def enabled(self) -> bool:
        return self.sdk is not None

    def get_current_trace_id(self) -> str | None:
        if self.sdk is None:
            return None
        try:
            result: str | None = self.sdk.get_current_trace_id()
            return result
        except Exception:
            return None

    def flush(self) -> None:
        if self.sdk is not None:
            try:
                self.sdk.flush()
            except Exception:
                pass


_global_client: LangfuseClient | None = None


def init_langfuse() -> LangfuseClient:
    """Initialise from env. Returns a disabled client if keys are absent."""
    global _global_client
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST", "http://localhost:3001")
    if not pk or not sk:
        _global_client = LangfuseClient(sdk=None)
        return _global_client
    sdk = Langfuse(public_key=pk, secret_key=sk, host=host)
    _global_client = LangfuseClient(sdk=sdk)
    return _global_client


def get_client() -> LangfuseClient:
    if _global_client is None:
        return init_langfuse()
    return _global_client


def get_current_trace_id() -> str | None:
    return get_client().get_current_trace_id()
