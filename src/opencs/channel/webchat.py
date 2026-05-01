from collections.abc import Callable
from datetime import datetime

from opencs.channel.adapter import ChannelAdapter
from opencs.channel.capabilities import ChannelCapabilities
from opencs.channel.exec_token import ExecutionToken
from opencs.channel.schema import ContentPart, InboundMessage, OutboundAction
from opencs.channel.types import ChannelConfig, HealthStatus, SendResult


class WebChatConfig(ChannelConfig):
    greeting: str = "hello"


class WebChatAdapter(ChannelAdapter):
    """In-process WebSocket-style adapter used for QA, replay smoke tests, and local dev."""

    channel_id = "webchat"
    capabilities = ChannelCapabilities(
        supports_text=True,
        supports_image=True,
        supports_voice=False,
        supports_card=True,
        supports_proactive_send=True,
        supports_history_fetch=False,
        max_message_length=8000,
    )

    def __init__(self) -> None:
        self.config: WebChatConfig | None = None
        self._subscribers: dict[str, list[Callable[[OutboundAction], None]]] = {}

    async def parse_inbound(self, raw_event: dict) -> InboundMessage:
        return InboundMessage(
            channel_id=self.channel_id,
            conversation_id=str(raw_event["conversation_id"]),
            customer_id=str(raw_event["customer_id"]),
            sender_kind="customer",
            content=[ContentPart(kind="text", text=str(raw_event["text"]))],
            timestamp=datetime.fromisoformat(str(raw_event["ts_iso"])),
            raw_payload=dict(raw_event),
            platform_meta={},
        )

    async def send(self, action: OutboundAction, token: ExecutionToken) -> SendResult:
        action_id = str(action.metadata["action_id"])
        token.verify(action_id=action_id)
        for cb in self._subscribers.get(action.conversation_id, ()):
            cb(action)
        return SendResult(delivered=True, platform_message_id=action_id)

    async def on_install(self, config: ChannelConfig) -> None:
        if config.channel_id != self.channel_id:
            raise ValueError(
                f"WebChatAdapter requires channel_id={self.channel_id!r}, "
                f"got {config.channel_id!r}"
            )
        self.config = (
            config if isinstance(config, WebChatConfig)
            else WebChatConfig(**config.model_dump())
        )

    async def health_check(self) -> HealthStatus:
        return HealthStatus(status="healthy")

    # -- WebChat-specific subscribe API (used by gateway/routes_webchat.py) --

    def subscribe(self, conversation_id: str, cb: Callable[[OutboundAction], None]) -> None:
        self._subscribers.setdefault(conversation_id, []).append(cb)

    def unsubscribe(self, conversation_id: str, cb: Callable[[OutboundAction], None]) -> None:
        if conversation_id in self._subscribers:
            self._subscribers[conversation_id] = [
                c for c in self._subscribers[conversation_id] if c is not cb
            ]
