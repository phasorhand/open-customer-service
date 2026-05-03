from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EvolutionDimension(StrEnum):
    SKILL = "skill"
    MEMORY = "memory"
    CRM_TOOL = "crm_tool"


class ProposalAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DEPRECATE = "deprecate"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    SHADOW_RUNNING = "shadow_running"
    HITL_PENDING = "hitl_pending"
    AUTO_PROMOTED = "auto_promoted"
    HITL_APPROVED = "hitl_approved"
    REJECTED = "rejected"


class GateDecision(StrEnum):
    AUTO_PROMOTE = "auto_promote"
    HITL_PENDING = "hitl_pending"
    REJECTED = "rejected"


class Proposal(BaseModel, frozen=True):
    id: str
    dimension: EvolutionDimension
    action: ProposalAction
    payload: dict[str, Any]
    evidence: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    risk_level: str
    status: ProposalStatus = ProposalStatus.PENDING
    replay_result: dict[str, Any] | None = None
    gate_decision: GateDecision | None = None
    reviewer: str | None = None
    rejection_note: str | None = None
    trace_id: str | None = None
