"""WeCom 客服 (微信客服) channel adapter.

Crypto and access-token plumbing reuses `wechatpy`; the kf-specific HTTP
endpoints (`kf/sync_msg`, `kf/send_msg`) are called directly with httpx
because wechatpy does not yet ship full kf coverage.
"""

import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar, cast

from opencs.channel.adapter import ChannelAdapter
from opencs.channel.capabilities import ChannelCapabilities
from opencs.channel.exec_token import ExecutionToken
from opencs.channel.schema import ContentPart, InboundMessage, OutboundAction
from opencs.channel.types import ChannelConfig, HealthStatus, SendResult


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


@dataclass(frozen=True)
class WecomKfMessage:
    """Single normalized message returned by `kf/sync_msg`."""

    msgid: str
    open_kfid: str
    external_userid: str
    msgtype: str  # "text" | "image" | ...
    send_time: int  # epoch seconds
    text: str | None = None
    media_url: str | None = None


MsgFetcher = Callable[[str, str | None], Awaitable[list[WecomKfMessage]]]
MsgSender = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class WecomCustomerServiceAdapter(ChannelAdapter):
    """企微客服 (微信客服) adapter."""

    channel_id: ClassVar[str] = "wecom_cs"
    capabilities: ClassVar[ChannelCapabilities] = ChannelCapabilities(
        supports_text=True,
        supports_image=True,
        supports_card=True,
        supports_proactive_send=False,
        supports_history_fetch=False,
        max_message_length=2000,
    )

    def __init__(
        self,
        msg_fetcher: MsgFetcher,
        msg_sender: MsgSender | None = None,
    ) -> None:
        self._fetch = msg_fetcher
        self._send_msg = msg_sender
        self._config: WecomCSConfig | None = None

    async def parse_inbound(self, raw_event: dict[str, object]) -> InboundMessage:
        decrypted = cast(dict[str, Any], raw_event["decrypted"])
        open_kfid = str(decrypted["OpenKfId"])
        next_cursor = decrypted.get("Token")
        cursor = str(next_cursor) if next_cursor is not None else None
        kf_msgs = await self._fetch(open_kfid, cursor)
        if not kf_msgs:
            raise ValueError(f"kf/sync_msg returned no messages for open_kfid={open_kfid!r}")
        head = kf_msgs[0]

        if head.msgtype == "text" and head.text:
            content = [ContentPart(kind="text", text=head.text)]
        elif head.msgtype == "image" and head.media_url:
            content = [ContentPart(kind="image", media_url=head.media_url, mime="image/jpeg")]
        else:
            content = [
                ContentPart(kind="text", text=f"[unsupported wecom msgtype: {head.msgtype}]")
            ]

        return InboundMessage(
            channel_id=self.channel_id,
            conversation_id=f"wecom:{open_kfid}:{head.external_userid}",
            customer_id=head.external_userid,
            sender_kind="customer",
            content=content,
            timestamp=datetime.fromtimestamp(head.send_time, tz=UTC),
            raw_payload=cast(dict[str, object], decrypted),
            platform_meta={
                "open_kfid": open_kfid,
                "external_userid": head.external_userid,
                "msgid": head.msgid,
            },
        )

    async def send(self, action: OutboundAction, token: ExecutionToken) -> SendResult:
        action_id = str(action.metadata["action_id"])
        token.verify(action_id=action_id)
        if action.kind != "reply":
            raise NotImplementedError(
                f"WecomCustomerServiceAdapter.send only supports kind='reply', got {action.kind!r}"
            )
        if self._send_msg is None:
            raise RuntimeError("WecomCustomerServiceAdapter has no msg_sender configured")
        if not action.content:
            raise ValueError("reply action requires content (validated by schema)")

        text = "\n".join(p.text for p in action.content if p.kind == "text" and p.text)
        if not text:
            raise NotImplementedError("non-text reply content not yet supported")

        payload: dict[str, object] = {
            "touser": str(action.metadata["external_userid"]),
            "open_kfid": str(action.metadata["open_kfid"]),
            "msgtype": "text",
            "text": {"content": text},
        }
        result = await self._send_msg(payload)
        return SendResult(delivered=True, platform_message_id=str(result["msgid"]))

    async def on_install(self, config: ChannelConfig) -> None:
        if not isinstance(config, WecomCSConfig):
            raise ValueError("WecomCustomerServiceAdapter requires WecomCSConfig")
        self._config = config

    async def health_check(self) -> HealthStatus:
        if self._config is None:
            return HealthStatus(status="degraded", detail="not configured")
        return HealthStatus(status="healthy")


__all__ = [
    "InvalidWecomSignatureError",
    "MsgFetcher",
    "MsgSender",
    "WecomCSConfig",
    "WecomCustomerServiceAdapter",
    "WecomKfMessage",
    "verify_callback_signature",
]
