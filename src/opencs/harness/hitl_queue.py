from dataclasses import dataclass, field

from opencs.harness.action_plan import ActionPlan


@dataclass
class HITLItem:
    plan: ActionPlan
    reason: str
    approved_by: str | None = None
    rejected_by: str | None = None
    rejection_note: str | None = None


class HITLQueue:
    """In-process HITL approval queue. Phase 7 replaces with Langfuse-backed impl."""

    def __init__(self) -> None:
        self._pending: dict[str, HITLItem] = {}

    def enqueue(self, plan: ActionPlan, *, reason: str) -> None:
        self._pending[plan.action_id] = HITLItem(plan=plan, reason=reason)

    def pending(self) -> list[HITLItem]:
        return list(self._pending.values())

    def approve(self, action_id: str, *, reviewer: str) -> HITLItem:
        item = self._pending.pop(action_id)
        item.approved_by = reviewer
        return item

    def reject(self, action_id: str, *, reviewer: str, note: str = "") -> HITLItem:
        item = self._pending.pop(action_id)
        item.rejected_by = reviewer
        item.rejection_note = note
        return item
