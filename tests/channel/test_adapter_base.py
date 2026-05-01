from datetime import UTC, datetime, timedelta

import pytest

from opencs.channel.adapter import ChannelAdapter
from opencs.channel.capabilities import ChannelCapabilities
from opencs.channel.exec_token import StubExecutionToken
from opencs.channel.schema import ContentPart, InboundMessage, OutboundAction
from opencs.channel.types import ChannelConfig, HealthStatus, SendResult


class _FakeAdapter(ChannelAdapter):
    channel_id = "fake"
    capabilities = ChannelCapabilities()

    def __init__(self) -> None:
        self.sent: list[OutboundAction] = []

    async def parse_inbound(self, raw_event: dict) -> InboundMessage:
        return InboundMessage(
            channel_id=self.channel_id,
            conversation_id=raw_event["conv"],
            customer_id=raw_event["cust"],
            sender_kind="customer",
            content=[ContentPart(kind="text", text=raw_event["text"])],
            timestamp=datetime.now(UTC),
            raw_payload=raw_event,
            platform_meta={},
        )

    async def send(self, action: OutboundAction, token) -> SendResult:
        token.verify(action_id=action.metadata["action_id"])
        self.sent.append(action)
        return SendResult(delivered=True, platform_message_id="m-1")

    async def on_install(self, config: ChannelConfig) -> None:
        return None

    async def health_check(self) -> HealthStatus:
        return HealthStatus(status="healthy")


async def test_adapter_round_trips_message() -> None:
    a = _FakeAdapter()
    msg = await a.parse_inbound({"conv": "c1", "cust": "u1", "text": "hi"})
    assert msg.text_concat() == "hi"


async def test_adapter_send_requires_valid_token() -> None:
    a = _FakeAdapter()
    action = OutboundAction(
        conversation_id="c1",
        kind="reply",
        content=[ContentPart(kind="text", text="ok")],
        target=None,
        metadata={"action_id": "act-1"},
    )
    good = StubExecutionToken("act-1", datetime.now(UTC) + timedelta(seconds=60))
    res = await a.send(action, good)
    assert res.delivered is True


async def test_adapter_send_rejects_wrong_token() -> None:
    from opencs.channel.exec_token import InvalidTokenError

    a = _FakeAdapter()
    action = OutboundAction(
        conversation_id="c1",
        kind="reply",
        content=[ContentPart(kind="text", text="ok")],
        target=None,
        metadata={"action_id": "act-1"},
    )
    bad = StubExecutionToken("act-2", datetime.now(UTC) + timedelta(seconds=60))
    with pytest.raises(InvalidTokenError):
        await a.send(action, bad)


def test_adapter_cannot_be_instantiated_without_methods() -> None:
    with pytest.raises(TypeError):
        ChannelAdapter()  # type: ignore[abstract]
