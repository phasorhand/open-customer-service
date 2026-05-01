import pytest

from opencs.channel.wecom_cs import (
    WecomCSConfig,
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
    from opencs.channel.wecom_cs import InvalidWecomSignatureError

    with pytest.raises(InvalidWecomSignatureError):
        verify_callback_signature(
            token="tok",
            timestamp="1700000000",
            nonce="abc",
            encrypt="ENCRYPTED",
            signature="deadbeef",
        )


from datetime import UTC, datetime

from opencs.channel.wecom_cs import (
    WecomCustomerServiceAdapter,
    WecomKfMessage,
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
