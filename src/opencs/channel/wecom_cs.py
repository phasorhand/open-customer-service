"""WeCom 客服 (微信客服) channel adapter.

Crypto and access-token plumbing reuses `wechatpy`; the kf-specific HTTP
endpoints (`kf/sync_msg`, `kf/send_msg`) are called directly with httpx
because wechatpy does not yet ship full kf coverage.
"""

import hashlib
from typing import ClassVar

from opencs.channel.types import ChannelConfig


class InvalidWecomSignatureError(Exception):
    """Raised when a WeCom callback signature does not match."""


class WecomCSConfig(ChannelConfig):
    corp_id: str
    secret: str
    token: str
    encoding_aes_key: str  # 43-char base64-ish per WeCom spec


def verify_callback_signature(
    *,
    token: str,
    timestamp: str,
    nonce: str,
    encrypt: str,
    signature: str,
) -> None:
    expected = hashlib.sha1(
        "".join(sorted([token, timestamp, nonce, encrypt])).encode()
    ).hexdigest()
    if expected != signature:
        raise InvalidWecomSignatureError("WeCom callback signature mismatch")


__all__ = [
    "InvalidWecomSignatureError",
    "WecomCSConfig",
    "verify_callback_signature",
]
