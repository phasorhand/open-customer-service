"""Production entry point: `uvicorn opencs.main:create_full_app --factory`.

Wires every SQLite store into one FastAPI app using env-driven paths.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from opencs.channel.registry import ChannelRegistry
from opencs.channel.webchat import WebChatAdapter
from opencs.evolution.crm_config_store import CRMConfigStore
from opencs.evolution.persistent_queue import PersistentHITLQueue
from opencs.evolution.proposal_store import ProposalStore
from opencs.gateway.app import create_app
from opencs.harness.audit_log import AuditLog
from opencs.tracing.langfuse_client import init_langfuse


def create_full_app() -> FastAPI:
    data_dir = Path(os.environ.get("OPENCS_DATA_DIR", "/data"))
    data_dir.mkdir(parents=True, exist_ok=True)

    init_langfuse()

    proposal_store = ProposalStore(db_path=str(data_dir / "evolution.db"))
    audit_log = AuditLog(db_path=str(data_dir / "audit.db"))
    hitl = PersistentHITLQueue(store=proposal_store)
    crm = CRMConfigStore(db_path=str(data_dir / "evolution.db"))

    registry = ChannelRegistry()
    registry.register(WebChatAdapter())

    return create_app(
        registry,
        webchat_handler=None,
        proposal_store=proposal_store,
        audit_log=audit_log,
        hitl_queue=hitl,
        crm_config_store=crm,
    )
