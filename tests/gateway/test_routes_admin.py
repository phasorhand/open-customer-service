from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from opencs.channel.registry import ChannelRegistry
from opencs.channel.webchat import WebChatAdapter
from opencs.evolution.crm_config_store import CRMConfigStore
from opencs.evolution.persistent_queue import PersistentHITLQueue
from opencs.evolution.proposal_store import ProposalStore
from opencs.evolution.types import (
    EvolutionDimension, Proposal, ProposalAction, ProposalStatus,
)
from opencs.gateway.app import create_app
from opencs.harness.audit_log import AuditLog


def _make_client() -> tuple[TestClient, ProposalStore, PersistentHITLQueue, AuditLog, CRMConfigStore]:
    proposal_store = ProposalStore(db_path=":memory:")
    audit_log = AuditLog(db_path=":memory:")
    hitl = PersistentHITLQueue(store=proposal_store)
    crm = CRMConfigStore(db_path=":memory:")
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    app = create_app(
        registry,
        webchat_handler=None,
        proposal_store=proposal_store,
        audit_log=audit_log,
        hitl_queue=hitl,
        crm_config_store=crm,
    )
    return TestClient(app), proposal_store, hitl, audit_log, crm


def _seed_proposal(
    store: ProposalStore,
    pid: str = "p-1",
    status: ProposalStatus = ProposalStatus.HITL_PENDING,
) -> Proposal:
    p = Proposal(
        id=pid,
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.CREATE,
        payload={"skill": "greet"},
        confidence=0.8,
        risk_level="medium",
        status=status,
    )
    store.save(p)
    return p


def test_list_proposals_returns_pending() -> None:
    client, store, _, _, _ = _make_client()
    _seed_proposal(store, "p-1", ProposalStatus.HITL_PENDING)
    _seed_proposal(store, "p-2", ProposalStatus.AUTO_PROMOTED)
    resp = client.get("/admin/proposals", params={"status": "hitl_pending"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "p-1"


def test_list_proposals_filters_by_dimension() -> None:
    client, store, _, _, _ = _make_client()
    p1 = Proposal(
        id="p-s", dimension=EvolutionDimension.SKILL, action=ProposalAction.CREATE,
        payload={}, confidence=0.5, risk_level="low", status=ProposalStatus.HITL_PENDING,
    )
    p2 = Proposal(
        id="p-m", dimension=EvolutionDimension.MEMORY, action=ProposalAction.CREATE,
        payload={}, confidence=0.5, risk_level="low", status=ProposalStatus.HITL_PENDING,
    )
    store.save(p1)
    store.save(p2)
    resp = client.get("/admin/proposals", params={"dimension": "memory"})
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["items"]]
    assert ids == ["p-m"]


def test_get_proposal_detail_returns_full_payload() -> None:
    client, store, _, _, _ = _make_client()
    _seed_proposal(store, "p-1")
    resp = client.get("/admin/proposals/p-1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "p-1"
    assert data["payload"] == {"skill": "greet"}


def test_get_proposal_404_when_unknown() -> None:
    client, _, _, _, _ = _make_client()
    resp = client.get("/admin/proposals/nope")
    assert resp.status_code == 404


def test_approve_proposal_updates_status() -> None:
    client, store, _, _, _ = _make_client()
    _seed_proposal(store, "p-1")
    resp = client.post("/admin/proposals/p-1/approve", json={"reviewer": "alice"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "hitl_approved"
    assert data["reviewer"] == "alice"
    assert store.get("p-1").status == ProposalStatus.HITL_APPROVED


def test_reject_proposal_updates_status_and_note() -> None:
    client, store, _, _, _ = _make_client()
    _seed_proposal(store, "p-1")
    resp = client.post(
        "/admin/proposals/p-1/reject",
        json={"reviewer": "bob", "note": "risky"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert data["rejection_note"] == "risky"


def test_approve_missing_reviewer_returns_422() -> None:
    client, store, _, _, _ = _make_client()
    _seed_proposal(store, "p-1")
    resp = client.post("/admin/proposals/p-1/approve", json={})
    assert resp.status_code == 422


def test_approve_unknown_proposal_returns_404() -> None:
    client, _, _, _, _ = _make_client()
    resp = client.post("/admin/proposals/nope/approve", json={"reviewer": "a"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Task 10: Audit log tests
# ---------------------------------------------------------------------------

def test_list_audit_log() -> None:
    from datetime import datetime
    from opencs.harness.action_plan import RiskTier
    from opencs.harness.audit_log import AuditEntry

    client, _, _, audit_log, _ = _make_client()
    for i in range(3):
        audit_log.append(AuditEntry(
            action_id=f"a-{i}", tool_id="t", risk_tier=RiskTier.GREEN,
            decision="auto_approved", actor="action_guard",
            ts=datetime(2026, 5, 1, 12, i, 0), note=None,
        ))
    resp = client.get("/admin/audit-log", params={"limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_list_audit_log_filtered_by_actor() -> None:
    from datetime import datetime
    from opencs.harness.action_plan import RiskTier
    from opencs.harness.audit_log import AuditEntry

    client, _, _, audit_log, _ = _make_client()
    for actor in ["alice", "bob", "alice"]:
        audit_log.append(AuditEntry(
            action_id="a", tool_id="t", risk_tier=RiskTier.GREEN,
            decision="auto_approved", actor=actor,
            ts=datetime(2026, 5, 1, 12, 0, 0), note=None,
        ))
    resp = client.get("/admin/audit-log", params={"actor": "alice"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


# ---------------------------------------------------------------------------
# Task 11: Replay endpoint tests
# ---------------------------------------------------------------------------

def test_admin_replays_post_delegates_to_engine() -> None:
    from unittest.mock import AsyncMock, MagicMock
    from opencs.replay.types import ReplayResult, Verdict

    proposal_store = ProposalStore(db_path=":memory:")
    audit_log = AuditLog(db_path=":memory:")
    hitl = PersistentHITLQueue(store=proposal_store)
    crm = CRMConfigStore(db_path=":memory:")
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    fake_engine = MagicMock()
    fake_engine.replay = AsyncMock(return_value=ReplayResult(
        session_id="s1", verdict=Verdict.BADCASE_FIXED,
        divergence_points=[], replay_event_count=2, baseline_event_count=2,
    ))
    app = create_app(
        registry, webchat_handler=None,
        replay_engine=fake_engine, proposal_store=proposal_store,
        audit_log=audit_log, hitl_queue=hitl, crm_config_store=crm,
    )
    client = TestClient(app)
    resp = client.post(
        "/admin/replays",
        json={"source_conversation_id": "c1", "mode": "what_if"},
    )
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "s1"


def test_admin_replays_503_without_engine() -> None:
    client, _, _, _, _ = _make_client()
    resp = client.post(
        "/admin/replays",
        json={"source_conversation_id": "c1", "mode": "what_if"},
    )
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Task 12: CRM config endpoint tests
# ---------------------------------------------------------------------------

def test_crm_config_get_returns_404_when_empty() -> None:
    client, _, _, _, _ = _make_client()
    resp = client.get("/admin/crm/config")
    assert resp.status_code == 404


def test_crm_config_put_and_get_roundtrip() -> None:
    client, _, _, _, _ = _make_client()
    resp = client.put(
        "/admin/crm/config",
        json={
            "base_url": "https://crm.example.com",
            "schema_json": "{}",
            "exposed_operations": ["getCustomer"],
        },
    )
    assert resp.status_code == 200
    resp2 = client.get("/admin/crm/config")
    assert resp2.status_code == 200
    assert resp2.json()["base_url"] == "https://crm.example.com"


def test_crm_validate_returns_detected_operations() -> None:
    client, _, _, _, _ = _make_client()
    schema = '{"openapi":"3.0","paths":{"/customer":{"get":{"operationId":"getCustomer"}}}}'
    resp = client.post(
        "/admin/crm/validate",
        json={"base_url": "https://crm.example.com", "schema_json": schema},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "getCustomer" in data["detected_operations"]


def test_crm_validate_rejects_bad_json() -> None:
    client, _, _, _, _ = _make_client()
    resp = client.post(
        "/admin/crm/validate",
        json={"base_url": "x", "schema_json": "not-json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert data["errors"]


# ---------------------------------------------------------------------------
# Task 13: Stats endpoint test
# ---------------------------------------------------------------------------

def test_stats_endpoint() -> None:
    from datetime import datetime
    from opencs.harness.action_plan import RiskTier
    from opencs.harness.audit_log import AuditEntry

    client, store, _, audit_log, _ = _make_client()
    _seed_proposal(store, "p-1", ProposalStatus.HITL_PENDING)
    _seed_proposal(store, "p-2", ProposalStatus.HITL_PENDING)
    _seed_proposal(store, "p-3", ProposalStatus.AUTO_PROMOTED)
    audit_log.append(AuditEntry(
        action_id="a-1", tool_id="t", risk_tier=RiskTier.GREEN,
        decision="auto_approved", actor="action_guard",
        ts=datetime.utcnow(), note=None,
    ))
    resp = client.get("/admin/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pending_proposals"] == 2
    assert len(data["recent_audit"]) == 1
