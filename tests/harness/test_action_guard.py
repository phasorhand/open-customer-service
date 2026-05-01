import pytest

from opencs.harness.action_guard import ActionGuard, ActionGuardDecision, GuardOutcome
from opencs.harness.action_plan import ActionPlan, RiskTier
from opencs.harness.audit_log import AuditLog
from opencs.harness.hitl_queue import HITLQueue
from opencs.harness.token import TokenFactory


def _guard() -> ActionGuard:
    return ActionGuard(
        token_factory=TokenFactory(secret_key=b"test", default_ttl_seconds=60),
        audit_log=AuditLog(db_path=":memory:"),
        hitl_queue=HITLQueue(),
    )


def _plan(tool_id: str = "crm.read", risk: RiskTier = RiskTier.GREEN) -> ActionPlan:
    return ActionPlan(
        action_id="act-1",
        tool_id=tool_id,
        args={"customer_id": "c1"},
        intent="test",
        risk_hint=risk,
    )


def test_green_plan_auto_approved_with_token() -> None:
    g = _guard()
    outcome = g.evaluate(_plan(risk=RiskTier.GREEN))
    assert outcome.decision == ActionGuardDecision.AUTO_APPROVED
    assert outcome.token is not None
    outcome.token.verify(action_id="act-1")


def test_yellow_plan_auto_approved_with_token() -> None:
    g = _guard()
    outcome = g.evaluate(_plan(risk=RiskTier.YELLOW))
    assert outcome.decision == ActionGuardDecision.AUTO_APPROVED
    assert outcome.token is not None


def test_orange_a_plan_auto_approved() -> None:
    g = _guard()
    outcome = g.evaluate(_plan(risk=RiskTier.ORANGE_A))
    assert outcome.decision == ActionGuardDecision.AUTO_APPROVED


def test_orange_b_plan_auto_approved() -> None:
    g = _guard()
    outcome = g.evaluate(_plan(risk=RiskTier.ORANGE_B))
    assert outcome.decision == ActionGuardDecision.AUTO_APPROVED


def test_orange_c_plan_queued_for_hitl() -> None:
    q = HITLQueue()
    g = ActionGuard(
        token_factory=TokenFactory(secret_key=b"t", default_ttl_seconds=60),
        audit_log=AuditLog(db_path=":memory:"),
        hitl_queue=q,
    )
    outcome = g.evaluate(_plan(risk=RiskTier.ORANGE_C))
    assert outcome.decision == ActionGuardDecision.HITL_QUEUED
    assert outcome.token is None
    assert len(q.pending()) == 1


def test_red_plan_queued_for_hitl() -> None:
    q = HITLQueue()
    g = ActionGuard(
        token_factory=TokenFactory(secret_key=b"t", default_ttl_seconds=60),
        audit_log=AuditLog(db_path=":memory:"),
        hitl_queue=q,
    )
    outcome = g.evaluate(_plan(risk=RiskTier.RED))
    assert outcome.decision == ActionGuardDecision.HITL_QUEUED
    assert outcome.token is None


def test_audit_log_entry_written() -> None:
    log = AuditLog(db_path=":memory:")
    g = ActionGuard(
        token_factory=TokenFactory(secret_key=b"t", default_ttl_seconds=60),
        audit_log=log,
        hitl_queue=HITLQueue(),
    )
    g.evaluate(_plan(risk=RiskTier.GREEN))
    entries = log.recent(limit=5)
    assert len(entries) == 1
    assert entries[0].action_id == "act-1"
    assert entries[0].decision == "auto_approved"
