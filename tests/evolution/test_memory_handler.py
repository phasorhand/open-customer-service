import pytest

from opencs.evolution.handlers.memory import (
    PII_KEYWORDS,
    MemoryApplyError,
    MemoryProposalHandler,
    _is_pii_payload,
)
from opencs.evolution.types import EvolutionDimension, Proposal, ProposalAction
from opencs.memory.memory_store import MemoryStore


def _memory_proposal(
    subject_id: str = "customer:u1",
    kind: str = "note",
    body: str = "VIP customer",
    extra: dict | None = None,
) -> Proposal:
    payload: dict = {"subject_id": subject_id, "kind": kind, "body": body}
    if extra:
        payload.update(extra)
    return Proposal(
        id="prop-mem-1",
        dimension=EvolutionDimension.MEMORY,
        action=ProposalAction.UPDATE,
        payload=payload,
        confidence=0.85,
        risk_level="low",
    )


@pytest.fixture
def memory_store() -> MemoryStore:
    return MemoryStore()


@pytest.fixture
def handler(memory_store: MemoryStore) -> MemoryProposalHandler:
    return MemoryProposalHandler(l2_store=memory_store.l2)


def test_apply_writes_to_l2(handler: MemoryProposalHandler, memory_store: MemoryStore) -> None:
    handler.apply(_memory_proposal())
    entries = memory_store.l2.get_by_subject("customer:u1")
    assert len(entries) == 1
    assert entries[0].body == "VIP customer"
    assert entries[0].kind == "note"


def test_apply_defaults_kind_to_note(
    handler: MemoryProposalHandler, memory_store: MemoryStore
) -> None:
    p = Proposal(
        id="prop-mem-2",
        dimension=EvolutionDimension.MEMORY,
        action=ProposalAction.CREATE,
        payload={"subject_id": "customer:u2", "body": "First contact"},
        confidence=0.8,
        risk_level="low",
    )
    handler.apply(p)
    entries = memory_store.l2.get_by_subject("customer:u2")
    assert entries[0].kind == "note"


def test_apply_raises_on_missing_subject_id(handler: MemoryProposalHandler) -> None:
    bad = Proposal(
        id="prop-bad",
        dimension=EvolutionDimension.MEMORY,
        action=ProposalAction.UPDATE,
        payload={"body": "no subject"},
        confidence=0.8,
        risk_level="low",
    )
    with pytest.raises(MemoryApplyError, match="subject_id"):
        handler.apply(bad)


def test_apply_raises_on_missing_body(handler: MemoryProposalHandler) -> None:
    bad = Proposal(
        id="prop-bad2",
        dimension=EvolutionDimension.MEMORY,
        action=ProposalAction.UPDATE,
        payload={"subject_id": "customer:u1"},
        confidence=0.8,
        risk_level="low",
    )
    with pytest.raises(MemoryApplyError, match="body"):
        handler.apply(bad)


def test_pii_keywords_set_is_exported() -> None:
    assert "phone" in PII_KEYWORDS
    assert "id_card" in PII_KEYWORDS
    assert "amount" in PII_KEYWORDS
    assert "email" in PII_KEYWORDS


def test_is_pii_payload_detects_phone() -> None:
    assert _is_pii_payload({"key": "phone_number", "body": "x"}) is True


def test_is_pii_payload_safe_payload() -> None:
    assert _is_pii_payload({"key": "session_summary", "body": "repeat buyer"}) is False
