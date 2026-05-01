from collections.abc import Awaitable, Callable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from opencs.channel.schema import InboundMessage, OutboundAction
from opencs.channel.webchat import WebChatAdapter

InboundHandler = Callable[[InboundMessage], Awaitable[None]]


def register_webchat_routes(
    app: FastAPI,
    adapter: WebChatAdapter,
    handler: InboundHandler | None,
) -> None:
    @app.websocket("/ws/webchat")
    async def webchat_ws(
        ws: WebSocket,
        conversation_id: str,
        customer_id: str,
    ) -> None:
        await ws.accept()

        async def push(action: OutboundAction) -> None:
            await ws.send_json(action.model_dump(mode="json"))

        def push_sync(action: OutboundAction) -> None:
            # WebChatAdapter.subscribe expects a sync callback; bridge via the running loop.
            import asyncio

            asyncio.create_task(push(action))

        adapter.subscribe(conversation_id, push_sync)
        try:
            while True:
                payload = await ws.receive_json()
                msg = await adapter.parse_inbound(
                    {
                        "conversation_id": conversation_id,
                        "customer_id": customer_id,
                        "text": payload.get("text", ""),
                        "ts_iso": payload.get("ts_iso", "1970-01-01T00:00:00+00:00"),
                    }
                )
                if handler is not None:
                    await handler(msg)
        except WebSocketDisconnect:
            pass
        finally:
            adapter.unsubscribe(conversation_id, push_sync)
