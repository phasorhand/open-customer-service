"""Composition root — wires real singletons and creates the FastAPI app.

Usage:
    uv run uvicorn opencs.main:create_app_with_defaults --factory --reload
"""

import os

from fastapi import FastAPI

from opencs.agents.cs_reply import CSReplyWorker
from opencs.agents.llm_client import LiteLLMClient
from opencs.agents.orchestrator import Orchestrator
from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import InboundMessage
from opencs.channel.webchat import WebChatAdapter
from opencs.gateway.app import create_app
from opencs.harness.action_guard import ActionGuard
from opencs.harness.audit_log import AuditLog
from opencs.harness.hitl_queue import HITLQueue
from opencs.harness.token import TokenFactory


def create_app_with_defaults() -> FastAPI:
    secret_key = os.environ.get("OPENCS_TOKEN_SECRET", "dev-secret-change-me").encode()
    model = os.environ.get("OPENCS_LLM_MODEL", "claude-sonnet-4-6")
    audit_db = os.environ.get("OPENCS_AUDIT_DB", "audit.db")

    registry = ChannelRegistry()
    registry.register(WebChatAdapter())

    guard = ActionGuard(
        token_factory=TokenFactory(secret_key=secret_key, default_ttl_seconds=30),
        audit_log=AuditLog(db_path=audit_db),
        hitl_queue=HITLQueue(),
    )

    llm = LiteLLMClient(default_model=model)
    worker = CSReplyWorker(llm=llm, model=model)
    orch = Orchestrator(workers=[worker], guard=guard, registry=registry)

    async def inbound_handler(msg: InboundMessage) -> None:
        await orch.handle(message=msg)

    return create_app(registry, webchat_handler=inbound_handler)
