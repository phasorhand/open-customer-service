from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from opencs.channel.schema import ContentPart, InboundMessage, OutboundAction


def test_content_part_text_round_trips() -> None:
    p = ContentPart(kind="text", text="hi")
    assert p.kind == "text"
    assert p.text == "hi"
    assert p.media_url is None


def test_content_part_image_requires_media_url() -> None:
    with pytest.raises(ValidationError):
        ContentPart(kind="image")


def test_inbound_message_minimal() -> None:
    msg = InboundMessage(
        channel_id="webchat",
        conversation_id="conv-1",
        customer_id="cust-1",
        sender_kind="customer",
        content=[ContentPart(kind="text", text="hello")],
        timestamp=datetime(2026, 5, 1, tzinfo=UTC),
        raw_payload={"raw": True},
        platform_meta={},
    )
    assert msg.text_concat() == "hello"


def test_inbound_message_text_concat_skips_non_text() -> None:
    msg = InboundMessage(
        channel_id="webchat",
        conversation_id="c",
        customer_id="u",
        sender_kind="customer",
        content=[
            ContentPart(kind="text", text="a"),
            ContentPart(kind="image", media_url="http://x/y.png"),
            ContentPart(kind="text", text="b"),
        ],
        timestamp=datetime(2026, 5, 1, tzinfo=UTC),
        raw_payload={},
        platform_meta={},
    )
    assert msg.text_concat() == "a\nb"


def test_inbound_message_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError):
        InboundMessage(
            channel_id="webchat",
            conversation_id="c",
            customer_id="u",
            sender_kind="customer",
            content=[ContentPart(kind="text", text="x")],
            timestamp=datetime(2026, 5, 1),  # naive
            raw_payload={},
            platform_meta={},
        )


def test_outbound_reply_requires_content() -> None:
    with pytest.raises(ValidationError):
        OutboundAction(
            conversation_id="c",
            kind="reply",
            content=None,
            target=None,
            metadata={},
        )


def test_outbound_add_tag_requires_target() -> None:
    with pytest.raises(ValidationError):
        OutboundAction(
            conversation_id="c",
            kind="add_tag",
            content=None,
            target=None,
            metadata={"tag": "vip"},
        )


def test_outbound_reply_ok() -> None:
    a = OutboundAction(
        conversation_id="c",
        kind="reply",
        content=[ContentPart(kind="text", text="ok")],
        target=None,
        metadata={},
    )
    assert a.kind == "reply"
