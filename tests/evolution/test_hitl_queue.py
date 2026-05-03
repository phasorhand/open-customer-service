import pytest

from opencs.evolution.hitl_queue import EvolutionHITLQueue
from opencs.evolution.types import EvolutionDimension, Proposal, ProposalAction


def _proposal(pid: str = "prop-1") -> Proposal:
    return Proposal(
        id=pid,
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.UPDATE,
        payload={"skill_id": "greet", "content": "# Greet"},
        confidence=0.9,
        risk_level="low",
    )


@pytest.fixture
def queue() -> EvolutionHITLQueue:
    return EvolutionHITLQueue()


def test_enqueue_and_pending(queue: EvolutionHITLQueue) -> None:
    queue.enqueue(_proposal(), reason="manual review required")
    items = queue.pending()
    assert len(items) == 1
    assert items[0].proposal.id == "prop-1"
    assert items[0].reason == "manual review required"


def test_pending_is_empty_initially(queue: EvolutionHITLQueue) -> None:
    assert queue.pending() == []


def test_approve_removes_from_pending(queue: EvolutionHITLQueue) -> None:
    queue.enqueue(_proposal())
    item = queue.approve("prop-1", reviewer="admin")
    assert item.approved_by == "admin"
    assert item.proposal.id == "prop-1"
    assert queue.pending() == []


def test_reject_removes_from_pending(queue: EvolutionHITLQueue) -> None:
    queue.enqueue(_proposal())
    item = queue.reject("prop-1", reviewer="admin", note="too risky")
    assert item.rejected_by == "admin"
    assert item.rejection_note == "too risky"
    assert queue.pending() == []


def test_approve_unknown_id_raises_key_error(queue: EvolutionHITLQueue) -> None:
    with pytest.raises(KeyError):
        queue.approve("nonexistent", reviewer="admin")


def test_reject_unknown_id_raises_key_error(queue: EvolutionHITLQueue) -> None:
    with pytest.raises(KeyError):
        queue.reject("nonexistent", reviewer="admin")


def test_multiple_proposals_independent(queue: EvolutionHITLQueue) -> None:
    queue.enqueue(_proposal("p-1"), reason="reason-1")
    queue.enqueue(_proposal("p-2"), reason="reason-2")
    assert len(queue.pending()) == 2
    queue.approve("p-1", reviewer="alice")
    assert len(queue.pending()) == 1
    assert queue.pending()[0].proposal.id == "p-2"


def test_default_reason_is_empty_string(queue: EvolutionHITLQueue) -> None:
    queue.enqueue(_proposal())
    assert queue.pending()[0].reason == ""
