from datetime import UTC, datetime, timedelta

import pytest

from opencs.channel.exec_token import StubExecutionToken
from opencs.channel.schema import ContentPart, OutboundAction
from opencs.channel.wecom_cs import (
    InvalidWecomSignatureError,
    WecomCSConfig,
    WecomCustomerServiceAdapter,
    WecomKfMessage,
    verify_callback_signature,
)


def test_config_round_trip() -> None:
    cfg = WecomCSConfig(
        channel_id="wecom_cs",
        corp_id="ww1234",
        secret="s",
        token="t",
        encoding_aes_key="k" * 43,
    )
    assert cfg.channel_id == "wecom_cs"
    assert cfg.corp_id == "ww1234"


def test_verify_callback_signature_accepts_correct() -> None:
    import hashlib

    token = "tok"
    timestamp = "1700000000"
    nonce = "abc"
    encrypt = "ENCRYPTED"
    sig = hashlib.sha1(
        "".join(sorted([token, timestamp, nonce, encrypt])).encode()
    ).hexdigest()
    verify_callback_signature(
        token=token, timestamp=timestamp, nonce=nonce, encrypt=encrypt, signature=sig
    )


def test_verify_callback_signature_rejects_wrong() -> None:
    with pytest.raises(InvalidWecomSignatureError):
        verify_callback_signature(
            token="tok",
            timestamp="1700000000",
            nonce="abc",
            encrypt="ENCRYPTED",
            signature="deadbeef",
        )


async def test_parse_inbound_uses_injected_fetcher() -> None:
    fetched: list[str] = []

    async def fake_fetcher(open_kfid: str, token: str | None) -> list[WecomKfMessage]:
        fetched.append(open_kfid)
        return [
            WecomKfMessage(
                msgid="m1",
                open_kfid=open_kfid,
                external_userid="u1",
                msgtype="text",
                send_time=int(datetime(2026, 5, 1, tzinfo=UTC).timestamp()),
                text="hello",
            )
        ]

    a = WecomCustomerServiceAdapter(msg_fetcher=fake_fetcher)
    msg = await a.parse_inbound(
        {
            "decrypted": {
                "ToUserName": "ww1234",
                "OpenKfId": "kf_xyz",
                "Event": "kf_msg_or_event",
                "Token": "next_cursor",
            }
        }
    )
    assert msg.channel_id == "wecom_cs"
    assert msg.text_concat() == "hello"
    assert msg.platform_meta["open_kfid"] == "kf_xyz"
    assert fetched == ["kf_xyz"]


async def test_send_calls_injected_sender_with_token_verified() -> None:
    sent: list[dict] = []

    async def fake_sender(payload: dict) -> dict:
        sent.append(payload)
        return {"msgid": "wm-1"}

    async def noop_fetcher(*_args, **_kwargs):
        return []

    a = WecomCustomerServiceAdapter(msg_fetcher=noop_fetcher, msg_sender=fake_sender)
    action = OutboundAction(
        conversation_id="wecom:kf_xyz:u1",
        kind="reply",
        content=[ContentPart(kind="text", text="hi back")],
        target=None,
        metadata={
            "action_id": "act-1",
            "open_kfid": "kf_xyz",
            "external_userid": "u1",
        },
    )
    token = StubExecutionToken("act-1", datetime.now(UTC) + timedelta(seconds=60))
    res = await a.send(action, token)
    assert res.delivered is True
    assert res.platform_message_id == "wm-1"
    assert sent == [
        {
            "touser": "u1",
            "open_kfid": "kf_xyz",
            "msgtype": "text",
            "text": {"content": "hi back"},
        }
    ]


async def test_send_rejects_non_reply_kind() -> None:
    async def noop(*_a, **_k):
        return []

    a = WecomCustomerServiceAdapter(msg_fetcher=noop, msg_sender=noop)
    action = OutboundAction(
        conversation_id="wecom:kf_xyz:u1",
        kind="add_tag",
        content=None,
        target="u1",
        metadata={"action_id": "act-2", "tag": "vip"},
    )
    token = StubExecutionToken("act-2", datetime.now(UTC) + timedelta(seconds=60))
    with pytest.raises(NotImplementedError):
        await a.send(action, token)
