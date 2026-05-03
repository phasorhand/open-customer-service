"""Composition root — wires real singletons and creates the FastAPI app.

Usage:
    uv run uvicorn opencs.main:create_app_with_defaults --factory --reload
"""

import os
from pathlib import Path

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
from opencs.memory.memory_store import MemoryStore
from opencs.skills.skill_repo import SkillRepo
from opencs.tools.api_tool import APITool
from opencs.tools.executor import ToolExecutor
from opencs.tools.mock_crm import router as mock_crm_router
from opencs.tools.registry import ToolRegistry

_BUNDLED_SKILLS_DIR = Path(__file__).parent / "skills" / "bundled"
_MOCK_CRM_BASE = "http://localhost:8001"


def _build_tool_registry(mock_crm_base: str) -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(APITool(
        tool_id="crm.get_customer",
        base_url=mock_crm_base,
        method="GET",
        path_template="/mock-crm/customers/{customer_id}",
        parameters_schema={"customer_id": {"type": "string"}},
        read_only=True,
    ))
    reg.register(APITool(
        tool_id="crm.get_order",
        base_url=mock_crm_base,
        method="GET",
        path_template="/mock-crm/orders/{order_id}",
        parameters_schema={"order_id": {"type": "string"}},
        read_only=True,
    ))
    return reg


def create_app_with_defaults() -> FastAPI:
    secret_key = os.environ.get("OPENCS_TOKEN_SECRET", "dev-secret-change-me").encode()
    model = os.environ.get("OPENCS_LLM_MODEL", "claude-sonnet-4-6")
    audit_db = os.environ.get("OPENCS_AUDIT_DB", "audit.db")
    memory_db = os.environ.get("OPENCS_MEMORY_DB", "memory.db")
    skills_dir = os.environ.get("OPENCS_SKILLS_DIR", str(_BUNDLED_SKILLS_DIR))
    mock_crm_base = os.environ.get("OPENCS_MOCK_CRM_BASE", _MOCK_CRM_BASE)

    channel_registry = ChannelRegistry()
    channel_registry.register(WebChatAdapter())

    guard = ActionGuard(
        token_factory=TokenFactory(secret_key=secret_key, default_ttl_seconds=30),
        audit_log=AuditLog(db_path=audit_db),
        hitl_queue=HITLQueue(),
    )

    memory = MemoryStore(l0_db=memory_db, l2_db=memory_db)
    skills = SkillRepo(skills_dir=skills_dir)
    llm = LiteLLMClient(default_model=model)
    worker = CSReplyWorker(llm=llm, model=model)

    tool_registry = _build_tool_registry(mock_crm_base)
    tool_executor = ToolExecutor(registry=tool_registry)

    orch = Orchestrator(
        workers=[worker],
        guard=guard,
        registry=channel_registry,
        memory_store=memory,
        skill_repo=skills,
        tool_executor=tool_executor,
    )

    async def inbound_handler(msg: InboundMessage) -> None:
        await orch.handle(message=msg)

    app = create_app(channel_registry, webchat_handler=inbound_handler)
    app.include_router(mock_crm_router)
    return app
