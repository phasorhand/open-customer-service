from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from opencs.evolution.types import EvolutionDimension, ProposalStatus
from opencs.gateway.admin_schemas import (
    ApprovalRequest,
    DecisionResponse,
    ProposalDetail,
    ProposalListResponse,
    ProposalSummary,
    RejectionRequest,
)

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
