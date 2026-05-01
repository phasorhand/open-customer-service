from datetime import UTC, datetime, timedelta

import pytest

from opencs.channel.exec_token import (
    ExecutionToken,
    InvalidTokenError,
    StubExecutionToken,
)


def test_stub_token_satisfies_protocol() -> None:
    t: ExecutionToken = StubExecutionToken(
        action_id="act-1",
        expires_at=datetime.now(UTC) + timedelta(seconds=60),
    )
    t.verify(action_id="act-1")


def test_stub_token_rejects_action_mismatch() -> None:
    t = StubExecutionToken(
        action_id="act-1",
        expires_at=datetime.now(UTC) + timedelta(seconds=60),
    )
    with pytest.raises(InvalidTokenError):
        t.verify(action_id="act-2")


def test_stub_token_rejects_expired() -> None:
    t = StubExecutionToken(
        action_id="act-1",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    with pytest.raises(InvalidTokenError):
        t.verify(action_id="act-1")
