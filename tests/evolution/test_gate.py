import uuid

import pytest

from opencs.evolution.gate import EvolutionGate
from opencs.evolution.types import (
    EvolutionDimension,
    GateDecision,
    Proposal,
    ProposalAction,
)
from opencs.harness.audit_log import AuditLog


def _skill_proposal(
    risk_level: str = "low",
    involves_orange_red: bool = False,
) -> Proposal:
    return Proposal(
        id=uuid.uuid4().hex,
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.UPDATE,
        payload={
            "skill_id": "greet",
            "content": "# Greet",
            "involves_orange_red_action": involves_orange_red,
        },
        confidence=0.9,
        risk_level=risk_level,
    )


def _memory_proposal(
    key: str = "turn_count",
    risk_level: str = "low",
    pii_detected: bool = False,
) -> Proposal:
    return Proposal(
        id=uuid.uuid4().hex,
        dimension=EvolutionDimension.MEMORY,
        action=ProposalAction.UPDATE,
        payload={"subject_id": "customer:u1", "kind": "note", "body": "repeat buyer", "key": key},
        evidence={"pii_detected": pii_detected},
        confidence=0.85,
        risk_level=risk_level,
    )


def _crm_tool_proposal(
    first_integration: bool = False,
    involves_write: bool = False,
    dry_run_success_count: int = 3,
) -> Proposal:
    return Proposal(
        id=uuid.uuid4().hex,
        dimension=EvolutionDimension.CRM_TOOL,
        action=ProposalAction.CREATE,
        payload={
            "tool_id": "crm.get_order",
            "first_integration": first_integration,
            "involves_write_operation": involves_write,
            "dry_run_success_count": dry_run_success_count,
        },
        confidence=0.88,
        risk_level="low",
    )


@pytest.fixture
def gate() -> EvolutionGate:
    return EvolutionGate(audit_log=AuditLog(db_path=":memory:"))


def test_skill_low_risk_auto_promotes(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_skill_proposal(risk_level="low"))
    assert decision == GateDecision.AUTO_PROMOTE


def test_skill_high_risk_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_skill_proposal(risk_level="high"))
    assert decision == GateDecision.HITL_PENDING


def test_skill_critical_risk_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_skill_proposal(risk_level="critical"))
    assert decision == GateDecision.HITL_PENDING


def test_skill_orange_red_action_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_skill_proposal(involves_orange_red=True))
    assert decision == GateDecision.HITL_PENDING


def test_memory_safe_key_auto_promotes(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_memory_proposal(key="session_summary"))
    assert decision == GateDecision.AUTO_PROMOTE


def test_memory_phone_key_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_memory_proposal(key="phone_number"))
    assert decision == GateDecision.HITL_PENDING


def test_memory_id_card_key_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_memory_proposal(key="id_card"))
    assert decision == GateDecision.HITL_PENDING


def test_memory_pii_detected_evidence_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_memory_proposal(pii_detected=True))
    assert decision == GateDecision.HITL_PENDING


def test_memory_amount_key_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_memory_proposal(key="amount"))
    assert decision == GateDecision.HITL_PENDING


def test_crm_tool_stable_auto_promotes(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_crm_tool_proposal(dry_run_success_count=3))
    assert decision == GateDecision.AUTO_PROMOTE


def test_crm_tool_first_integration_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_crm_tool_proposal(first_integration=True, dry_run_success_count=3))
    assert decision == GateDecision.HITL_PENDING


def test_crm_tool_write_operation_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_crm_tool_proposal(involves_write=True))
    assert decision == GateDecision.HITL_PENDING


def test_crm_tool_insufficient_dry_runs_requires_hitl(gate: EvolutionGate) -> None:
    decision = gate.evaluate(_crm_tool_proposal(dry_run_success_count=2))
    assert decision == GateDecision.HITL_PENDING


def test_gate_appends_audit_entry(gate: EvolutionGate) -> None:
    gate.evaluate(_skill_proposal())
    entries = gate._audit_log.recent(limit=10)
    assert len(entries) >= 1
    assert entries[0].actor == "evolution_gate"


def test_gate_stamps_current_trace_id(monkeypatch) -> None:
    from opencs.evolution.gate import EvolutionGate
    from opencs.evolution.types import (
        EvolutionDimension,
        Proposal,
        ProposalAction,
    )
    from opencs.harness.audit_log import AuditLog

    monkeypatch.setattr(
        "opencs.evolution.gate.get_current_trace_id",
        lambda: "trace-stamped",
    )
    gate = EvolutionGate(audit_log=AuditLog(db_path=":memory:"))
    p = Proposal(
        id="p-1", dimension=EvolutionDimension.SKILL, action=ProposalAction.CREATE,
        payload={"skill": "x"}, confidence=0.8, risk_level="low",
    )
    stamped = gate.stamp_trace_id(p)
    assert stamped.trace_id == "trace-stamped"
