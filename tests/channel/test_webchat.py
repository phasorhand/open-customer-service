from datetime import UTC, datetime, timedelta

from opencs.channel.exec_token import StubExecutionToken
from opencs.channel.schema import ContentPart, OutboundAction
from opencs.channel.types import ChannelConfig
from opencs.channel.webchat import WebChatAdapter, WebChatConfig


async def test_parse_inbound_builds_message() -> None:
    a = WebChatAdapter()
    msg = await a.parse_inbound(
        {
            "conversation_id": "c1",
            "customer_id": "u1",
            "text": "hello",
            "ts_iso": "2026-05-01T00:00:00+00:00",
        }
    )
    assert msg.channel_id == "webchat"
    assert msg.text_concat() == "hello"
    assert msg.platform_meta == {}


async def test_send_emits_to_subscribers_and_returns_delivered() -> None:
    a = WebChatAdapter()
    received: list[OutboundAction] = []
    a.subscribe("c1", received.append)

    action = OutboundAction(
        conversation_id="c1",
        kind="reply",
        content=[ContentPart(kind="text", text="ok")],
        target=None,
        metadata={"action_id": "act-1"},
    )
    token = StubExecutionToken("act-1", datetime.now(UTC) + timedelta(seconds=60))
    res = await a.send(action, token)
    assert res.delivered is True
    assert received == [action]


async def test_on_install_records_config() -> None:
    a = WebChatAdapter()
    cfg = WebChatConfig(channel_id="webchat", greeting="hi")
    await a.on_install(cfg)
    assert a.config is cfg


async def test_on_install_rejects_wrong_channel_config() -> None:
    a = WebChatAdapter()
    import pytest
    with pytest.raises(ValueError):
        await a.on_install(ChannelConfig(channel_id="other"))


async def test_health_check_is_healthy() -> None:
    a = WebChatAdapter()
    h = await a.health_check()
    assert h.status == "healthy"
