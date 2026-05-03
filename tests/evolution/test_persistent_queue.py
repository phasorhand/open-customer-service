from __future__ import annotations

import pytest

from opencs.evolution.persistent_queue import PersistentHITLQueue
from opencs.evolution.proposal_store import ProposalStore
from opencs.evolution.types import (
    EvolutionDimension,
    Proposal,
    ProposalAction,
    ProposalStatus,
)


def _proposal(pid: str = "p-1") -> Proposal:
    return Proposal(
        id=pid,
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.CREATE,
        payload={"x": 1},
        confidence=0.7,
        risk_level="medium",
    )


def test_enqueue_sets_hitl_pending_status() -> None:
    store = ProposalStore(db_path=":memory:")
    queue = PersistentHITLQueue(store=store)
    p = _proposal()
    store.save(p)
    queue.enqueue(p, reason="needs review")
    loaded = store.get(p.id)
    assert loaded is not None
    assert loaded.status == ProposalStatus.HITL_PENDING


def test_pending_returns_only_hitl_pending() -> None:
    store = ProposalStore(db_path=":memory:")
    queue = PersistentHITLQueue(store=store)
    p1 = _proposal("p-1")
    p2 = _proposal("p-2")
    store.save(p1)
    store.save(p2)
    queue.enqueue(p1)
    queue.enqueue(p2)
    pending = queue.pending()
    assert {p.id for p in pending} == {"p-1", "p-2"}


def test_approve_updates_status_and_reviewer() -> None:
    store = ProposalStore(db_path=":memory:")
    queue = PersistentHITLQueue(store=store)
    p = _proposal()
    store.save(p)
    queue.enqueue(p)
    approved = queue.approve(p.id, reviewer="alice")
    assert approved.status == ProposalStatus.HITL_APPROVED
    assert approved.reviewer == "alice"
    assert queue.pending() == []


def test_reject_updates_status_and_note() -> None:
    store = ProposalStore(db_path=":memory:")
    queue = PersistentHITLQueue(store=store)
    p = _proposal()
    store.save(p)
    queue.enqueue(p)
    rejected = queue.reject(p.id, reviewer="bob", note="too risky")
    assert rejected.status == ProposalStatus.REJECTED
    assert rejected.reviewer == "bob"
    assert rejected.rejection_note == "too risky"


def test_approve_unknown_proposal_raises() -> None:
    store = ProposalStore(db_path=":memory:")
    queue = PersistentHITLQueue(store=store)
    with pytest.raises(KeyError):
        queue.approve("nope", reviewer="alice")


def test_queue_survives_reinstantiation() -> None:
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        store1 = ProposalStore(db_path=path)
        q1 = PersistentHITLQueue(store=store1)
        p = _proposal()
        store1.save(p)
        q1.enqueue(p)
        store2 = ProposalStore(db_path=path)
        q2 = PersistentHITLQueue(store=store2)
        pending = q2.pending()
        assert len(pending) == 1
        assert pending[0].id == p.id
    finally:
        os.unlink(path)
