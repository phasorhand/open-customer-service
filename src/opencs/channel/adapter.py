from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar

from opencs.channel.capabilities import ChannelCapabilities
from opencs.channel.exec_token import ExecutionToken
from opencs.channel.schema import InboundMessage, OutboundAction
from opencs.channel.types import ChannelConfig, HealthStatus, MediaRef, SendResult


class ChannelAdapter(ABC):
    """Unified contract every IM-platform integration must satisfy.

    Adapters are pure protocol translators: no LLM calls, no Memory writes,
    no business decisions. Outbound side-effects require a Harness-issued
    `ExecutionToken` — calling `send` without one is a type error.
    """

    channel_id: ClassVar[str]
    capabilities: ClassVar[ChannelCapabilities]

    @abstractmethod
    async def parse_inbound(self, raw_event: dict) -> InboundMessage:
        """Translate a platform-native callback payload into an InboundMessage.

        Implementations are responsible for signature verification, decryption,
        and (where the platform requires it) follow-up message-fetch calls.
        """

    @abstractmethod
    async def send(
        self,
        action: OutboundAction,
        token: ExecutionToken,
    ) -> SendResult:
        """Translate OutboundAction into a platform-native send call.

        MUST call `token.verify(action_id=...)` before any side effect.
        """

    @abstractmethod
    async def on_install(self, config: ChannelConfig) -> None:
        """Persist install-time config (callback URL, app secret, etc)."""

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Lightweight liveness probe."""

    # -- Optional capabilities --------------------------------------------------

    async def fetch_history(
        self,
        conversation_id: str,
        since: datetime,
    ) -> list[InboundMessage]:
        raise NotImplementedError(f"{self.channel_id} does not support history fetch")

    async def upload_media(self, file: bytes, mime: str) -> MediaRef:
        raise NotImplementedError(f"{self.channel_id} does not support media upload")

    async def add_tag(self, customer_id: str, tag: str) -> None:
        raise NotImplementedError(f"{self.channel_id} does not support tagging")
