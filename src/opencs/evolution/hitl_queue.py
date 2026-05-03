from __future__ import annotations

from dataclasses import dataclass

from opencs.evolution.types import Proposal


@dataclass
class EvolutionHITLItem:
    proposal: Proposal
    reason: str
    approved_by: str | None = None
    rejected_by: str | None = None
    rejection_note: str | None = None


class EvolutionHITLQueue:
    def __init__(self) -> None:
        self._pending: dict[str, EvolutionHITLItem] = {}

    def enqueue(self, proposal: Proposal, reason: str = "") -> None:
        self._pending[proposal.id] = EvolutionHITLItem(proposal=proposal, reason=reason)

    def pending(self) -> list[EvolutionHITLItem]:
        return list(self._pending.values())

    def approve(self, proposal_id: str, *, reviewer: str) -> EvolutionHITLItem:
        item = self._pending.pop(proposal_id)
        item.approved_by = reviewer
        return item

    def reject(
        self, proposal_id: str, *, reviewer: str, note: str = ""
    ) -> EvolutionHITLItem:
        item = self._pending.pop(proposal_id)
        item.rejected_by = reviewer
        item.rejection_note = note
        return item
