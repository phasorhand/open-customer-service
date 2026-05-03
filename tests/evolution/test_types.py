from opencs.evolution.types import (
    EvolutionDimension,
    GateDecision,
    Proposal,
    ProposalAction,
    ProposalStatus,
)


def test_evolution_dimension_values() -> None:
    assert EvolutionDimension.SKILL == "skill"
    assert EvolutionDimension.MEMORY == "memory"
    assert EvolutionDimension.CRM_TOOL == "crm_tool"


def test_proposal_action_values() -> None:
    assert ProposalAction.CREATE == "create"
    assert ProposalAction.UPDATE == "update"
    assert ProposalAction.DEPRECATE == "deprecate"


def test_proposal_status_values() -> None:
    assert ProposalStatus.PENDING == "pending"
    assert ProposalStatus.SHADOW_RUNNING == "shadow_running"
    assert ProposalStatus.HITL_PENDING == "hitl_pending"
    assert ProposalStatus.AUTO_PROMOTED == "auto_promoted"
    assert ProposalStatus.HITL_APPROVED == "hitl_approved"
    assert ProposalStatus.REJECTED == "rejected"


def test_gate_decision_values() -> None:
    assert GateDecision.AUTO_PROMOTE == "auto_promote"
    assert GateDecision.HITL_PENDING == "hitl_pending"
    assert GateDecision.REJECTED == "rejected"


def test_proposal_defaults() -> None:
    p = Proposal(
        id="prop-1",
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.UPDATE,
        payload={"skill_id": "greet", "content": "# Greet\nSay hello."},
        confidence=0.9,
        risk_level="low",
    )
    assert p.status == ProposalStatus.PENDING
    assert p.evidence == {}
    assert p.replay_result is None
    assert p.gate_decision is None
    assert p.reviewer is None
    assert p.rejection_note is None


def test_proposal_is_frozen() -> None:
    import pytest

    p = Proposal(
        id="prop-2",
        dimension=EvolutionDimension.MEMORY,
        action=ProposalAction.CREATE,
        payload={"subject_id": "customer:u1", "kind": "note", "body": "VIP"},
        confidence=0.8,
        risk_level="low",
    )
    with pytest.raises(Exception):
        p.id = "mutated"  # type: ignore[misc]


def test_proposal_with_replay_result() -> None:
    p = Proposal(
        id="prop-3",
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.UPDATE,
        payload={"skill_id": "refund", "content": "# Refund\nProcess refunds."},
        confidence=0.95,
        risk_level="low",
        replay_result={"verdict": "badcase_fixed", "session_id": "sess-abc"},
        gate_decision=GateDecision.AUTO_PROMOTE,
    )
    assert p.replay_result is not None
    assert p.replay_result["verdict"] == "badcase_fixed"
    assert p.gate_decision == GateDecision.AUTO_PROMOTE
