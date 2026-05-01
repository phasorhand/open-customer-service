from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from opencs.channel.exec_token import StubExecutionToken
from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import ContentPart, InboundMessage, OutboundAction
from opencs.channel.webchat import WebChatAdapter
from opencs.gateway.app import create_app


def _echo_handler(adapter: WebChatAdapter):
    async def handle(msg: InboundMessage) -> None:
        action = OutboundAction(
            conversation_id=msg.conversation_id,
            kind="reply",
            content=[ContentPart(kind="text", text=f"echo:{msg.text_concat()}")],
            target=None,
            metadata={"action_id": f"echo-{msg.conversation_id}"},
        )
        token = StubExecutionToken(
            action_id=f"echo-{msg.conversation_id}",
            expires_at=datetime.now(UTC) + timedelta(seconds=10),
        )
        await adapter.send(action, token)

    return handle


def test_webchat_ws_echo() -> None:
    registry = ChannelRegistry()
    webchat = WebChatAdapter()
    registry.register(webchat)
    app = create_app(registry, webchat_handler=_echo_handler(webchat))
    client = TestClient(app)

    with client.websocket_connect("/ws/webchat?conversation_id=c1&customer_id=u1") as ws:
        ws.send_json({"text": "hello", "ts_iso": "2026-05-01T00:00:00+00:00"})
        reply = ws.receive_json()
        assert reply["kind"] == "reply"
        assert reply["content"][0]["text"] == "echo:hello"


def test_create_app_health_endpoint() -> None:
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    app = create_app(registry, webchat_handler=None)
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "channels": ["webchat"]}
