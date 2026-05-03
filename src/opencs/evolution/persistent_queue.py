from __future__ import annotations

from opencs.evolution.proposal_store import ProposalStore
from opencs.evolution.types import Proposal, ProposalStatus


class PersistentHITLQueue:
    """HITL queue backed by ProposalStore. The proposal's status field IS the queue state."""

    def __init__(self, *, store: ProposalStore) -> None:
        self._store = store

    def enqueue(self, proposal: Proposal, reason: str = "") -> None:
        updated = proposal.model_copy(update={"status": ProposalStatus.HITL_PENDING})
        self._store.save(updated)

    def pending(self) -> list[Proposal]:
        return self._store.list_by_status(ProposalStatus.HITL_PENDING)

    def approve(self, proposal_id: str, *, reviewer: str) -> Proposal:
        current = self._store.get(proposal_id)
        if current is None or current.status != ProposalStatus.HITL_PENDING:
            raise KeyError(f"No pending proposal with id={proposal_id}")
        updated = current.model_copy(update={
            "status": ProposalStatus.HITL_APPROVED,
            "reviewer": reviewer,
        })
        self._store.save(updated)
        return updated

    def reject(self, proposal_id: str, *, reviewer: str, note: str = "") -> Proposal:
        current = self._store.get(proposal_id)
        if current is None or current.status != ProposalStatus.HITL_PENDING:
            raise KeyError(f"No pending proposal with id={proposal_id}")
        updated = current.model_copy(update={
            "status": ProposalStatus.REJECTED,
            "reviewer": reviewer,
            "rejection_note": note or None,
        })
        self._store.save(updated)
        return updated
