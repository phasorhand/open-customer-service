from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI

from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import InboundMessage
from opencs.channel.webchat import WebChatAdapter
from opencs.channel.wecom_cs import WecomCustomerServiceAdapter
from opencs.gateway.routes_admin import router as admin_router
from opencs.gateway.routes_replay import router as replay_router
from opencs.gateway.routes_webchat import register_webchat_routes
from opencs.gateway.routes_wecom import register_wecom_routes

InboundHandler = Callable[[InboundMessage], Awaitable[None]]


def create_app(
    registry: ChannelRegistry,
    *,
    webchat_handler: InboundHandler | None,
    wecom_handler: InboundHandler | None = None,
    replay_engine: Any | None = None,
    proposal_store: Any | None = None,
    audit_log: Any | None = None,
    hitl_queue: Any | None = None,
    crm_config_store: Any | None = None,
) -> FastAPI:
    app = FastAPI(title="OpenCS Gateway", version="0.1.0")
    app.state.replay_engine = replay_engine
    app.state.proposal_store = proposal_store
    app.state.audit_log = audit_log
    app.state.hitl_queue = hitl_queue
    app.state.crm_config_store = crm_config_store

    @app.get("/health")
    async def health() -> dict[str, object]:
        return {"status": "ok", "channels": sorted(registry.ids())}

    app.include_router(replay_router)
    app.include_router(admin_router)

    if "webchat" in registry.ids():
        webchat = registry.get("webchat")
        assert isinstance(webchat, WebChatAdapter)
        register_webchat_routes(app, webchat, webchat_handler)

    if "wecom_cs" in registry.ids():
        if wecom_handler is None:
            raise ValueError("wecom_cs channel registered but no wecom_handler provided")
        wecom = registry.get("wecom_cs")
        assert isinstance(wecom, WecomCustomerServiceAdapter)
        register_wecom_routes(app, wecom, wecom_handler)

    return app


def create_default_app() -> FastAPI:
    """Entry point for `uvicorn opencs.gateway.app:create_default_app --factory`."""
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    return create_app(registry, webchat_handler=None)
