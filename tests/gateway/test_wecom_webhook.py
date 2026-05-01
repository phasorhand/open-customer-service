from datetime import UTC, datetime
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from opencs.channel.registry import ChannelRegistry
from opencs.channel.wecom_cs import WecomCSConfig, WecomCustomerServiceAdapter, WecomKfMessage
from opencs.gateway.app import create_app


class _FakeCrypto:
    """Stub wechatpy crypto used in tests; bypasses real decryption."""

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def check_signature(self, *_args, **_kwargs) -> None:
        return None

    def decrypt_message(self, msg, signature, timestamp, nonce):
        return (
            "<xml><ToUserName>ww1234</ToUserName>"
            "<OpenKfId>kf_xyz</OpenKfId>"
            "<Event>kf_msg_or_event</Event>"
            "<Token>cursor-1</Token></xml>"
        )


async def _fake_fetch(open_kfid: str, cursor: str | None) -> list[WecomKfMessage]:
    return [
        WecomKfMessage(
            msgid="m1",
            open_kfid=open_kfid,
            external_userid="u1",
            msgtype="text",
            send_time=int(datetime(2026, 5, 1, tzinfo=UTC).timestamp()),
            text="ping",
        )
    ]


def test_wecom_webhook_post_invokes_handler(monkeypatch) -> None:
    monkeypatch.setattr("opencs.gateway.routes_wecom.WeChatCrypto", _FakeCrypto)

    registry = ChannelRegistry()
    adapter = WecomCustomerServiceAdapter(msg_fetcher=_fake_fetch)
    registry.register(adapter)

    handler = AsyncMock()
    app = create_app(registry, webchat_handler=None, wecom_handler=handler)

    import asyncio
    asyncio.get_event_loop().run_until_complete(
        adapter.on_install(
            WecomCSConfig(
                channel_id="wecom_cs",
                corp_id="ww1234",
                secret="s",
                token="tok",
                encoding_aes_key="k" * 43,
            )
        )
    )

    client = TestClient(app)
    r = client.post(
        "/webhook/wecom_cs",
        params={"msg_signature": "sig", "timestamp": "1700000000", "nonce": "n"},
        content="<xml><Encrypt>ENC</Encrypt></xml>",
        headers={"content-type": "application/xml"},
    )
    assert r.status_code == 200
    assert r.text == "success"
    handler.assert_awaited_once()
    inbound = handler.await_args.args[0]
    assert inbound.channel_id == "wecom_cs"
    assert inbound.text_concat() == "ping"


def test_wecom_webhook_get_echoes(monkeypatch) -> None:
    class _CryptoEcho:
        def __init__(self, *_a, **_k) -> None: ...
        def check_signature(self, *_a, **_k) -> None: ...
        def verify_url(self, *_a, **_k) -> str:
            return "echo-payload"

    monkeypatch.setattr("opencs.gateway.routes_wecom.WeChatCrypto", _CryptoEcho)

    registry = ChannelRegistry()
    adapter = WecomCustomerServiceAdapter(msg_fetcher=_fake_fetch)
    registry.register(adapter)
    import asyncio
    asyncio.get_event_loop().run_until_complete(
        adapter.on_install(
            WecomCSConfig(
                channel_id="wecom_cs",
                corp_id="ww1234",
                secret="s",
                token="tok",
                encoding_aes_key="k" * 43,
            )
        )
    )

    app = create_app(registry, webchat_handler=None, wecom_handler=AsyncMock())
    client = TestClient(app)
    r = client.get(
        "/webhook/wecom_cs",
        params={
            "msg_signature": "sig",
            "timestamp": "1700000000",
            "nonce": "n",
            "echostr": "challenge",
        },
    )
    assert r.status_code == 200
    assert r.text == "echo-payload"
