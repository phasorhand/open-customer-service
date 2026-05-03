import pytest

from opencs.evolution.proposal_store import ProposalStore
from opencs.evolution.types import (
    EvolutionDimension,
    GateDecision,
    Proposal,
    ProposalAction,
    ProposalStatus,
)


@pytest.fixture
def store() -> ProposalStore:
    return ProposalStore(db_path=":memory:")


def _proposal(pid: str = "prop-1", dim: EvolutionDimension = EvolutionDimension.SKILL) -> Proposal:
    return Proposal(
        id=pid,
        dimension=dim,
        action=ProposalAction.UPDATE,
        payload={"skill_id": "greet", "content": "# Greet"},
        confidence=0.9,
        risk_level="low",
    )


def test_save_and_get(store: ProposalStore) -> None:
    p = _proposal()
    store.save(p)
    retrieved = store.get("prop-1")
    assert retrieved is not None
    assert retrieved.id == "prop-1"
    assert retrieved.dimension == EvolutionDimension.SKILL


def test_get_nonexistent_returns_none(store: ProposalStore) -> None:
    assert store.get("does-not-exist") is None


def test_update_status(store: ProposalStore) -> None:
    store.save(_proposal())
    store.update_status("prop-1", ProposalStatus.SHADOW_RUNNING)
    updated = store.get("prop-1")
    assert updated is not None
    assert updated.status == ProposalStatus.SHADOW_RUNNING


def test_update_gate_decision_auto(store: ProposalStore) -> None:
    store.save(_proposal())
    store.update_gate_decision(
        "prop-1",
        gate_decision=GateDecision.AUTO_PROMOTE,
        status=ProposalStatus.AUTO_PROMOTED,
    )
    p = store.get("prop-1")
    assert p is not None
    assert p.gate_decision == GateDecision.AUTO_PROMOTE
    assert p.status == ProposalStatus.AUTO_PROMOTED


def test_update_gate_decision_hitl_with_reviewer(store: ProposalStore) -> None:
    store.save(_proposal())
    store.update_gate_decision(
        "prop-1",
        gate_decision=GateDecision.REJECTED,
        status=ProposalStatus.REJECTED,
        reviewer="admin",
        rejection_note="Too risky",
    )
    p = store.get("prop-1")
    assert p is not None
    assert p.reviewer == "admin"
    assert p.rejection_note == "Too risky"


def test_attach_replay_result(store: ProposalStore) -> None:
    store.save(_proposal())
    store.attach_replay_result(
        "prop-1",
        {"verdict": "badcase_fixed", "session_id": "sess-xyz", "divergence_count": 0},
    )
    p = store.get("prop-1")
    assert p is not None
    assert p.replay_result is not None
    assert p.replay_result["verdict"] == "badcase_fixed"


def test_list_by_status(store: ProposalStore) -> None:
    store.save(_proposal("p-1"))
    store.save(_proposal("p-2"))
    store.save(_proposal("p-3", dim=EvolutionDimension.MEMORY))
    store.update_status("p-2", ProposalStatus.HITL_PENDING)

    pending = store.list_by_status(ProposalStatus.PENDING)
    hitl = store.list_by_status(ProposalStatus.HITL_PENDING)
    assert len(pending) == 2
    assert len(hitl) == 1
    assert hitl[0].id == "p-2"
