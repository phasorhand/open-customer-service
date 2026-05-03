from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from opencs.channel.schema import OutboundAction
from opencs.channel.types import HealthStatus, SendResult

if TYPE_CHECKING:
    from opencs.channel.exec_token import ExecutionToken


@dataclass
class CapturedSend:
    action: OutboundAction
    timestamp: datetime


class ReadOnlyChannelAdapter:
    """Channel adapter that captures sends without dispatching. Used during replay."""

    channel_id: str = "replay_readonly"

    def __init__(self) -> None:
        self.captured: list[CapturedSend] = []

    async def send(self, action: OutboundAction, token: ExecutionToken) -> SendResult:
        self.captured.append(CapturedSend(action=action, timestamp=datetime.now(UTC)))
        return SendResult(delivered=True, platform_message_id="replay-captured")

    async def health_check(self) -> HealthStatus:
        return HealthStatus(status="healthy", detail="read-only replay adapter")
