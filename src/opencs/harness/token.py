import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from opencs.channel.exec_token import InvalidTokenError as _BaseInvalidTokenError


class InvalidTokenError(_BaseInvalidTokenError):
    """Raised when a HarnessToken fails HMAC verification."""


def _canonical_args_hash(args: dict[str, object]) -> bytes:
    canonical = json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).digest()


def _compute_signature(
    action_id: str,
    args_hash: bytes,
    expires_at: datetime,
    secret_key: bytes,
) -> bytes:
    message = (
        action_id.encode()
        + b"|"
        + args_hash.hex().encode()
        + b"|"
        + expires_at.isoformat().encode()
    )
    return hmac.new(secret_key, message, digestmod=hashlib.sha256).digest()


@dataclass(frozen=True)
class HarnessToken:
    """HMAC-signed execution token. Satisfies the ExecutionToken Protocol."""

    action_id: str
    args_hash: bytes
    expires_at: datetime
    signature: bytes
    _secret_key: bytes | None = field(default=None, repr=False, compare=False)

    def verify(self, *, action_id: str, secret_key: bytes | None = None) -> None:
        if action_id != self.action_id:
            raise InvalidTokenError(
                f"action_id mismatch: token={self.action_id!r} call={action_id!r}"
            )
        if datetime.now(UTC) >= self.expires_at:
            raise InvalidTokenError("token expired")
        # Use the explicitly provided key, or fall back to the one embedded at issue time.
        # If neither is available the signature cannot be verified — treat as invalid.
        effective_key = secret_key if secret_key is not None else self._secret_key
        if effective_key is None:
            raise InvalidTokenError("token signature cannot be verified: no secret key available")
        expected = _compute_signature(
            self.action_id, self.args_hash, self.expires_at, effective_key
        )
        if not hmac.compare_digest(expected, self.signature):
            raise InvalidTokenError("token signature mismatch")


class TokenFactory:
    """Issues HarnessToken instances signed with a fixed secret key."""

    def __init__(self, *, secret_key: bytes, default_ttl_seconds: int = 30) -> None:
        self._secret = secret_key
        self._ttl = default_ttl_seconds

    def issue(self, *, action_id: str, args: dict[str, object]) -> HarnessToken:
        expires_at = datetime.now(UTC) + timedelta(seconds=self._ttl)
        args_hash = _canonical_args_hash(args)
        signature = _compute_signature(action_id, args_hash, expires_at, self._secret)
        return HarnessToken(
            action_id=action_id,
            args_hash=args_hash,
            expires_at=expires_at,
            signature=signature,
            _secret_key=self._secret,
        )

    def verify(self, token: HarnessToken, *, action_id: str) -> None:
        token.verify(action_id=action_id, secret_key=self._secret)
