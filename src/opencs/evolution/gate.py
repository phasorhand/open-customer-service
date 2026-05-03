from __future__ import annotations

from datetime import UTC, datetime

from opencs.evolution.types import EvolutionDimension, GateDecision, Proposal
from opencs.harness.action_plan import RiskTier
from opencs.harness.audit_log import AuditEntry, AuditLog
from opencs.tracing.langfuse_client import get_current_trace_id

_PII_KEYS: frozenset[str] = frozenset({
    "phone", "id_card", "id_number", "address", "email",
    "amount", "commitment", "mobile", "phone_number",
})


class EvolutionGate:
    def __init__(self, *, audit_log: AuditLog) -> None:
        self._audit_log = audit_log

    def evaluate(self, proposal: Proposal) -> GateDecision:
        decision = self._policy(proposal)
        self._audit_log.append(AuditEntry(
            action_id=f"evo-{proposal.id[:12]}",
            tool_id=f"evolution.{proposal.dimension}",
            risk_tier=RiskTier.GREEN,
            decision=str(decision),
            actor="evolution_gate",
            ts=datetime.now(UTC),
            note=f"dimension={proposal.dimension} action={proposal.action} "
                 f"risk={proposal.risk_level}",
        ))
        return decision

    def _policy(self, proposal: Proposal) -> GateDecision:
        if proposal.dimension == EvolutionDimension.SKILL:
            return self._skill_policy(proposal)
        if proposal.dimension == EvolutionDimension.MEMORY:
            return self._memory_policy(proposal)
        if proposal.dimension == EvolutionDimension.CRM_TOOL:
            return self._crm_tool_policy(proposal)
        return GateDecision.HITL_PENDING

    def _skill_policy(self, proposal: Proposal) -> GateDecision:
        if proposal.payload.get("involves_orange_red_action"):
            return GateDecision.HITL_PENDING
        if proposal.risk_level in ("high", "critical"):
            return GateDecision.HITL_PENDING
        return GateDecision.AUTO_PROMOTE

    def _memory_policy(self, proposal: Proposal) -> GateDecision:
        if proposal.evidence.get("pii_detected"):
            return GateDecision.HITL_PENDING
        key = str(proposal.payload.get("key", ""))
        if any(pii in key.lower() for pii in _PII_KEYS):
            return GateDecision.HITL_PENDING
        if proposal.risk_level in ("high", "critical"):
            return GateDecision.HITL_PENDING
        return GateDecision.AUTO_PROMOTE

    def _crm_tool_policy(self, proposal: Proposal) -> GateDecision:
        if proposal.payload.get("first_integration"):
            return GateDecision.HITL_PENDING
        if proposal.payload.get("involves_write_operation"):
            return GateDecision.HITL_PENDING
        dry_run_count = int(proposal.payload.get("dry_run_success_count", 0))
        if dry_run_count < 3:
            return GateDecision.HITL_PENDING
        return GateDecision.AUTO_PROMOTE

    def stamp_trace_id(self, proposal: Proposal) -> Proposal:
        """Attach the current Langfuse trace_id to the proposal (if available)."""
        trace_id = get_current_trace_id()
        if trace_id is None:
            return proposal
        return proposal.model_copy(update={"trace_id": trace_id})
