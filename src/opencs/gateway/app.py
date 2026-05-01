from collections.abc import Awaitable, Callable

from fastapi import FastAPI

from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import InboundMessage
from opencs.channel.webchat import WebChatAdapter
from opencs.gateway.routes_webchat import register_webchat_routes

InboundHandler = Callable[[InboundMessage], Awaitable[None]]


def create_app(
    registry: ChannelRegistry,
    *,
    webchat_handler: InboundHandler | None,
) -> FastAPI:
    app = FastAPI(title="OpenCS Gateway", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, object]:
        return {"status": "ok", "channels": sorted(registry.ids())}

    if "webchat" in registry.ids():
        webchat = registry.get("webchat")
        assert isinstance(webchat, WebChatAdapter)
        register_webchat_routes(app, webchat, webchat_handler)

    return app


def create_default_app() -> FastAPI:
    """Entry point for `uvicorn opencs.gateway.app:create_default_app --factory`."""
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    return create_app(registry, webchat_handler=None)
