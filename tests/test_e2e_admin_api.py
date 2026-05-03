"""E2E Admin API: proposal lifecycle through approve and reject flows."""

import httpx

from opencs.channel.registry import ChannelRegistry
from opencs.channel.webchat import WebChatAdapter
from opencs.evolution.persistent_queue import PersistentHITLQueue
from opencs.evolution.proposal_store import ProposalStore
from opencs.evolution.types import (
    EvolutionDimension,
    Proposal,
    ProposalAction,
)
from opencs.gateway.app import create_app
from opencs.harness.audit_log import AuditLog


def _make_app():
    """Create a FastAPI app wired with in-memory stores."""
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    store = ProposalStore(db_path=":memory:")
    queue = PersistentHITLQueue(store=store)
    audit = AuditLog(db_path=":memory:")
    app = create_app(
        registry,
        webchat_handler=None,
        proposal_store=store,
        hitl_queue=queue,
        audit_log=audit,
    )
    return app, store, queue


def _sample_proposal(pid: str = "prop-e2e-1") -> Proposal:
    return Proposal(
        id=pid,
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.CREATE,
        payload={"skill_id": "greet", "content": "# Greet\nSay hello."},
        evidence={"source": "unit-test"},
        confidence=0.85,
        risk_level="low",
    )


async def test_proposal_lifecycle_approve() -> None:
    app, _store, queue = _make_app()
    transport = httpx.ASGITransport(app=app)

    # Enqueue a proposal so it lands in HITL_PENDING state
    proposal = _sample_proposal("prop-approve-1")
    queue.enqueue(proposal, reason="needs human review")

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Verify proposal shows up in the pending list
        resp = await client.get("/admin/proposals", params={"status": "hitl_pending"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["id"] == "prop-approve-1"
        assert body["items"][0]["status"] == "hitl_pending"

        # 2. Approve the proposal
        resp = await client.post(
            "/admin/proposals/prop-approve-1/approve",
            json={"reviewer": "admin"},
        )
        assert resp.status_code == 200
        decision = resp.json()
        assert decision["id"] == "prop-approve-1"
        assert decision["status"] == "hitl_approved"
        assert decision["reviewer"] == "admin"

        # 3. Verify the pending list is now empty
        resp = await client.get("/admin/proposals", params={"status": "hitl_pending"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


async def test_proposal_lifecycle_reject() -> None:
    app, _store, queue = _make_app()
    transport = httpx.ASGITransport(app=app)

    proposal = _sample_proposal("prop-reject-1")
    queue.enqueue(proposal, reason="needs human review")

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Verify proposal shows up in the pending list
        resp = await client.get("/admin/proposals", params={"status": "hitl_pending"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["id"] == "prop-reject-1"

        # 2. Reject the proposal with a note
        resp = await client.post(
            "/admin/proposals/prop-reject-1/reject",
            json={"reviewer": "admin", "note": "Not ready for production"},
        )
        assert resp.status_code == 200
        decision = resp.json()
        assert decision["id"] == "prop-reject-1"
        assert decision["status"] == "rejected"
        assert decision["reviewer"] == "admin"
        assert decision["rejection_note"] == "Not ready for production"

        # 3. Verify the pending list is now empty
        resp = await client.get("/admin/proposals", params={"status": "hitl_pending"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
