"""Phase 1 stub for the Harness-issued ExecutionToken.

The real signed token (HMAC + arg-hash binding) is implemented in Phase 2
(`opencs.harness`). This module pins the *protocol* so all adapter signatures
already require a token and Phase 2 only swaps the implementation.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


class InvalidTokenError(Exception):
    """Raised when a token is expired, action-mismatched, or otherwise invalid."""


@runtime_checkable
class ExecutionToken(Protocol):
    """Contract every Harness-issued token must satisfy."""

    action_id: str
    expires_at: datetime

    def verify(self, *, action_id: str) -> None:
        """Raise `InvalidTokenError` if the token cannot authorize `action_id` now."""
        ...


@dataclass(frozen=True)
class StubExecutionToken:
    """Phase-1-only token. Trusts its own fields; do not use in production."""

    action_id: str
    expires_at: datetime

    def verify(self, *, action_id: str) -> None:
        if action_id != self.action_id:
            raise InvalidTokenError(
                f"token action_id mismatch: token={self.action_id!r} call={action_id!r}"
            )
        if datetime.now(UTC) >= self.expires_at:
            raise InvalidTokenError("token expired")
