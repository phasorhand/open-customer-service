from __future__ import annotations

import json as _json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel as _BaseModel

from opencs.evolution.crm_config_store import CRMConfig
from opencs.evolution.types import EvolutionDimension, ProposalStatus
from opencs.gateway.admin_schemas import (
    ApprovalRequest,
    AuditLogEntry,
    AuditLogListResponse,
    CRMConfigRequest,
    CRMConfigResponse,
    CRMValidateRequest,
    CRMValidateResponse,
    DecisionResponse,
    ProposalDetail,
    ProposalListResponse,
    ProposalSummary,
    RejectionRequest,
    StatsResponse,
)
from opencs.replay.types import ReplayMode, ReplayOverrides, ReplayScope, ReplaySession

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_proposal_store(request: Request):
    store = getattr(request.app.state, "proposal_store", None)
    if store is None:
        raise HTTPException(503, "ProposalStore not configured")
    return store


def _require_hitl_queue(request: Request):
    q = getattr(request.app.state, "hitl_queue", None)
    if q is None:
        raise HTTPException(503, "HITL queue not configured")
    return q


@router.get("/proposals", response_model=ProposalListResponse)
async def list_proposals(
    request: Request,
    status: ProposalStatus | None = Query(default=None),
    dimension: EvolutionDimension | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ProposalListResponse:
    store = _require_proposal_store(request)
    items = store.list(status=status, dimension=dimension, limit=limit, offset=offset)
    total = (
        store.count_by_status(status) if status is not None
        else len(store.list(limit=10_000, offset=0))
    )
    return ProposalListResponse(
        items=[
            ProposalSummary(
                id=p.id, dimension=p.dimension, action=p.action, status=p.status,
                risk_level=p.risk_level, confidence=p.confidence, trace_id=p.trace_id,
            )
            for p in items
        ],
        total=total, limit=limit, offset=offset,
    )


@router.get("/proposals/{proposal_id}", response_model=ProposalDetail)
async def get_proposal(proposal_id: str, request: Request) -> ProposalDetail:
    store = _require_proposal_store(request)
    p = store.get(proposal_id)
    if p is None:
        raise HTTPException(404, f"Proposal {proposal_id} not found")
    return ProposalDetail(
        id=p.id, dimension=p.dimension, action=p.action, status=p.status,
        risk_level=p.risk_level, confidence=p.confidence, payload=p.payload,
        evidence=p.evidence, replay_result=p.replay_result,
        gate_decision=p.gate_decision, reviewer=p.reviewer,
        rejection_note=p.rejection_note, trace_id=p.trace_id,
    )


@router.post("/proposals/{proposal_id}/approve", response_model=DecisionResponse)
async def approve_proposal(
    proposal_id: str, body: ApprovalRequest, request: Request,
) -> DecisionResponse:
    queue = _require_hitl_queue(request)
    try:
        updated = queue.approve(proposal_id, reviewer=body.reviewer)
    except KeyError:
        raise HTTPException(404, f"No pending proposal with id={proposal_id}")
    return DecisionResponse(
        id=updated.id, status=updated.status,
        reviewer=updated.reviewer, rejection_note=updated.rejection_note,
    )


@router.post("/proposals/{proposal_id}/reject", response_model=DecisionResponse)
async def reject_proposal(
    proposal_id: str, body: RejectionRequest, request: Request,
) -> DecisionResponse:
    queue = _require_hitl_queue(request)
    try:
        updated = queue.reject(proposal_id, reviewer=body.reviewer, note=body.note)
    except KeyError:
        raise HTTPException(404, f"No pending proposal with id={proposal_id}")
    return DecisionResponse(
        id=updated.id, status=updated.status,
        reviewer=updated.reviewer, rejection_note=updated.rejection_note,
    )


# ---------------------------------------------------------------------------
# Task 10: Audit log endpoint
# ---------------------------------------------------------------------------

def _require_audit_log(request: Request):
    log = getattr(request.app.state, "audit_log", None)
    if log is None:
        raise HTTPException(503, "AuditLog not configured")
    return log


@router.get("/audit-log", response_model=AuditLogListResponse)
async def list_audit_log(
    request: Request,
    actor: str | None = Query(default=None),
    decision: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> AuditLogListResponse:
    log = _require_audit_log(request)
    entries = log.list(
        actor=actor, decision=decision, since=since, until=until,
        limit=limit, offset=offset,
    )
    total = log.count(actor=actor, decision=decision)
    return AuditLogListResponse(
        items=[
            AuditLogEntry(
                action_id=e.action_id, tool_id=e.tool_id,
                risk_tier=int(e.risk_tier), decision=e.decision,
                actor=e.actor, ts=e.ts, note=e.note,
            ) for e in entries
        ],
        total=total, limit=limit, offset=offset,
    )


# ---------------------------------------------------------------------------
# Task 11: Replay endpoints under /admin
# ---------------------------------------------------------------------------

class AdminReplayRequest(_BaseModel):
    source_conversation_id: str
    mode: ReplayMode = ReplayMode.WHAT_IF
    scope: ReplayScope = ReplayScope.CONVERSATION
    overrides: ReplayOverrides = ReplayOverrides()


class AdminReplayResponse(_BaseModel):
    session_id: str
    verdict: str
    divergence_count: int
    baseline_event_count: int
    replay_event_count: int


def _require_replay_engine(request: Request):
    engine = getattr(request.app.state, "replay_engine", None)
    if engine is None:
        raise HTTPException(503, "ReplayEngine not configured")
    return engine


@router.post("/replays", response_model=AdminReplayResponse)
async def admin_post_replay(
    body: AdminReplayRequest, request: Request,
) -> AdminReplayResponse:
    engine = _require_replay_engine(request)
    session = ReplaySession(
        source_conversation_id=body.source_conversation_id,
        mode=body.mode, scope=body.scope, overrides=body.overrides,
    )
    result = await engine.replay(session)
    return AdminReplayResponse(
        session_id=result.session_id,
        verdict=str(result.verdict),
        divergence_count=len(result.divergence_points),
        baseline_event_count=result.baseline_event_count,
        replay_event_count=result.replay_event_count,
    )


# ---------------------------------------------------------------------------
# Task 12: CRM config endpoints
# ---------------------------------------------------------------------------

def _require_crm_store(request: Request):
    store = getattr(request.app.state, "crm_config_store", None)
    if store is None:
        raise HTTPException(503, "CRMConfigStore not configured")
    return store


@router.get("/crm/config", response_model=CRMConfigResponse)
async def get_crm_config(request: Request) -> CRMConfigResponse:
    store = _require_crm_store(request)
    cfg = store.get()
    if cfg is None:
        raise HTTPException(404, "No CRM config set")
    return CRMConfigResponse(
        base_url=cfg.base_url,
        schema_json=cfg.schema_json,
        exposed_operations=cfg.exposed_operations,
    )


@router.put("/crm/config", response_model=CRMConfigResponse)
async def put_crm_config(
    body: CRMConfigRequest, request: Request,
) -> CRMConfigResponse:
    store = _require_crm_store(request)
    store.save(CRMConfig(
        base_url=body.base_url,
        schema_json=body.schema_json,
        exposed_operations=list(body.exposed_operations),
    ))
    return CRMConfigResponse(
        base_url=body.base_url,
        schema_json=body.schema_json,
        exposed_operations=body.exposed_operations,
    )


def _detect_operations(schema_json: str) -> tuple[bool, list[str], list[str]]:
    try:
        doc = _json.loads(schema_json)
    except _json.JSONDecodeError as e:
        return False, [], [f"schema_json is not valid JSON: {e}"]
    if not isinstance(doc, dict) or "paths" not in doc:
        return False, [], ["schema_json missing 'paths' key (not an OpenAPI doc?)"]
    ops: list[str] = []
    for path_val in doc["paths"].values():
        if not isinstance(path_val, dict):
            continue
        for op in path_val.values():
            if isinstance(op, dict) and "operationId" in op:
                ops.append(op["operationId"])
    return True, ops, []


@router.post("/crm/validate", response_model=CRMValidateResponse)
async def validate_crm(body: CRMValidateRequest) -> CRMValidateResponse:
    ok, ops, errs = _detect_operations(body.schema_json)
    return CRMValidateResponse(ok=ok, detected_operations=ops, errors=errs)


# ---------------------------------------------------------------------------
# Task 13: /admin/stats endpoint
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsResponse)
async def get_stats(request: Request) -> StatsResponse:
    store = _require_proposal_store(request)
    log = _require_audit_log(request)
    pending = store.count_by_status(ProposalStatus.HITL_PENDING)
    recent_entries = log.list(limit=10, offset=0)
    recent = [
        AuditLogEntry(
            action_id=e.action_id, tool_id=e.tool_id,
            risk_tier=int(e.risk_tier), decision=e.decision,
            actor=e.actor, ts=e.ts, note=e.note,
        )
        for e in recent_entries
    ]
    approved_today = sum(1 for e in recent_entries if e.decision == "auto_approved")
    rejected_today = sum(1 for e in recent_entries if e.decision == "rejected")
    return StatsResponse(
        pending_proposals=pending,
        approved_today=approved_today,
        rejected_today=rejected_today,
        recent_audit=recent,
    )
