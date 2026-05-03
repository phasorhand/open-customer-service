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


def test_proposal_store_persists_trace_id() -> None:
    from opencs.evolution.proposal_store import ProposalStore
    from opencs.evolution.types import (
        EvolutionDimension,
        Proposal,
        ProposalAction,
    )
    store = ProposalStore(db_path=":memory:")
    p = Proposal(
        id="p-trace-1",
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.CREATE,
        payload={"x": 1},
        confidence=0.8,
        risk_level="low",
        trace_id="trace-abc-123",
    )
    store.save(p)
    loaded = store.get("p-trace-1")
    assert loaded is not None
    assert loaded.trace_id == "trace-abc-123"


def test_proposal_store_trace_id_default_none() -> None:
    from opencs.evolution.proposal_store import ProposalStore
    from opencs.evolution.types import (
        EvolutionDimension,
        Proposal,
        ProposalAction,
    )
    store = ProposalStore(db_path=":memory:")
    p = Proposal(
        id="p-notrace",
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.CREATE,
        payload={},
        confidence=0.5,
        risk_level="low",
    )
    store.save(p)
    loaded = store.get("p-notrace")
    assert loaded is not None
    assert loaded.trace_id is None


def test_proposal_store_list_with_filters() -> None:
    from opencs.evolution.proposal_store import ProposalStore
    from opencs.evolution.types import (
        EvolutionDimension,
        Proposal,
        ProposalAction,
        ProposalStatus,
    )
    store = ProposalStore(db_path=":memory:")
    for i, (dim, status) in enumerate([
        (EvolutionDimension.SKILL, ProposalStatus.HITL_PENDING),
        (EvolutionDimension.MEMORY, ProposalStatus.HITL_PENDING),
        (EvolutionDimension.SKILL, ProposalStatus.AUTO_PROMOTED),
    ]):
        store.save(Proposal(
            id=f"p-{i}", dimension=dim, action=ProposalAction.CREATE,
            payload={}, confidence=0.5, risk_level="low", status=status,
        ))
    pending_all = store.list(status=ProposalStatus.HITL_PENDING)
    assert len(pending_all) == 2
    pending_skill = store.list(
        status=ProposalStatus.HITL_PENDING, dimension=EvolutionDimension.SKILL,
    )
    assert len(pending_skill) == 1
    page = store.list(limit=2, offset=0)
    assert len(page) == 2


def test_proposal_store_count_by_status() -> None:
    from opencs.evolution.proposal_store import ProposalStore
    from opencs.evolution.types import (
        EvolutionDimension,
        Proposal,
        ProposalAction,
        ProposalStatus,
    )
    store = ProposalStore(db_path=":memory:")
    for i in range(3):
        store.save(Proposal(
            id=f"p-{i}", dimension=EvolutionDimension.SKILL,
            action=ProposalAction.CREATE, payload={},
            confidence=0.5, risk_level="low",
            status=ProposalStatus.HITL_PENDING,
        ))
    assert store.count_by_status(ProposalStatus.HITL_PENDING) == 3
    assert store.count_by_status(ProposalStatus.AUTO_PROMOTED) == 0
