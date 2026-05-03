from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from opencs.evolution.types import (
    EvolutionDimension,
    GateDecision,
    ProposalAction,
    ProposalStatus,
)


class ProposalSummary(BaseModel):
    id: str
    dimension: EvolutionDimension
    action: ProposalAction
    status: ProposalStatus
    risk_level: str
    confidence: float
    trace_id: str | None = None


class ProposalListResponse(BaseModel):
    items: list[ProposalSummary]
    total: int
    limit: int
    offset: int


class ProposalDetail(BaseModel):
    id: str
    dimension: EvolutionDimension
    action: ProposalAction
    status: ProposalStatus
    risk_level: str
    confidence: float
    payload: dict[str, Any]
    evidence: dict[str, Any]
    replay_result: dict[str, Any] | None = None
    gate_decision: GateDecision | None = None
    reviewer: str | None = None
    rejection_note: str | None = None
    trace_id: str | None = None


class ApprovalRequest(BaseModel):
    reviewer: str = Field(min_length=1)


class RejectionRequest(BaseModel):
    reviewer: str = Field(min_length=1)
    note: str = ""


class DecisionResponse(BaseModel):
    id: str
    status: ProposalStatus
    reviewer: str | None
    rejection_note: str | None


class AuditLogEntry(BaseModel):
    action_id: str
    tool_id: str
    risk_tier: int
    decision: str
    actor: str
    ts: datetime
    note: str | None = None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    pending_proposals: int
    approved_today: int
    rejected_today: int
    recent_audit: list[AuditLogEntry]


class CRMConfigRequest(BaseModel):
    base_url: str = Field(min_length=1)
    schema_json: str
    exposed_operations: list[str] = Field(default_factory=list)


class CRMConfigResponse(BaseModel):
    base_url: str
    schema_json: str
    exposed_operations: list[str]


class CRMValidateRequest(BaseModel):
    base_url: str = Field(min_length=1)
    schema_json: str


class CRMValidateResponse(BaseModel):
    ok: bool
    detected_operations: list[str]
    errors: list[str] = Field(default_factory=list)
