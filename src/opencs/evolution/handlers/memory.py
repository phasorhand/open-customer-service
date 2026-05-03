from __future__ import annotations

from opencs.evolution.types import Proposal
from opencs.memory.l2_store import L2MemoryStore, MemoryEntry

PII_KEYWORDS: frozenset[str] = frozenset({
    "phone", "id_card", "id_number", "address", "email",
    "amount", "commitment", "mobile", "phone_number",
})


def _is_pii_payload(payload: dict[str, object]) -> bool:
    key = str(payload.get("key", "")).lower()
    return any(pii in key for pii in PII_KEYWORDS)


class MemoryApplyError(Exception):
    pass


class MemoryProposalHandler:
    def __init__(self, *, l2_store: L2MemoryStore) -> None:
        self._l2 = l2_store

    def apply(self, proposal: Proposal) -> None:
        subject_id = proposal.payload.get("subject_id")
        if not subject_id:
            raise MemoryApplyError("proposal.payload must contain 'subject_id'")
        body = proposal.payload.get("body")
        if not body:
            raise MemoryApplyError("proposal.payload must contain 'body'")
        kind = str(proposal.payload.get("kind", "note"))
        self._l2.write(MemoryEntry(
            subject_id=str(subject_id),
            kind=kind,
            body=str(body),
        ))
