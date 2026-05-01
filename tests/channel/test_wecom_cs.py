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
