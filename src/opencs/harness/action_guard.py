from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from opencs.harness.action_plan import ActionPlan, RiskTier
from opencs.harness.audit_log import AuditEntry, AuditLog
from opencs.harness.hitl_queue import HITLQueue
from opencs.harness.token import HarnessToken, TokenFactory

_AUTO_TIERS = {RiskTier.GREEN, RiskTier.YELLOW, RiskTier.ORANGE_A, RiskTier.ORANGE_B}
_HITL_TIERS = {RiskTier.ORANGE_C, RiskTier.RED}


class ActionGuardDecision(str, Enum):
    AUTO_APPROVED = "auto_approved"
    HITL_QUEUED = "hitl_queued"
    REJECTED = "rejected"


@dataclass
class GuardOutcome:
    decision: ActionGuardDecision
    token: HarnessToken | None
    reason: str


class ActionGuard:
    """Classifies ActionPlan risk, issues ExecutionToken or queues HITL, writes AuditLog."""

    def __init__(
        self,
        *,
        token_factory: TokenFactory,
        audit_log: AuditLog,
        hitl_queue: HITLQueue,
    ) -> None:
        self._tf = token_factory
        self._log = audit_log
        self._hitl = hitl_queue

    def evaluate(self, plan: ActionPlan) -> GuardOutcome:
        tier = plan.risk_hint  # MVP: trust the Worker's risk hint directly

        if tier in _AUTO_TIERS:
            token = self._tf.issue(action_id=plan.action_id, args=plan.args)
            outcome = GuardOutcome(
                decision=ActionGuardDecision.AUTO_APPROVED,
                token=token,
                reason=f"tier={tier.name} is auto-approved",
            )
        else:
            self._hitl.enqueue(plan, reason=f"tier={tier.name} requires HITL approval")
            outcome = GuardOutcome(
                decision=ActionGuardDecision.HITL_QUEUED,
                token=None,
                reason=f"tier={tier.name} queued for human review",
            )

        self._log.append(AuditEntry(
            action_id=plan.action_id,
            tool_id=plan.tool_id,
            risk_tier=tier,
            decision=outcome.decision.value,
            actor="action_guard",
            ts=datetime.now(UTC),
            note=outcome.reason,
        ))
        return outcome
