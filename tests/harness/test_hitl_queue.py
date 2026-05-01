import pytest

from opencs.harness.action_plan import ActionPlan, RiskTier
from opencs.harness.hitl_queue import HITLQueue


def _plan(action_id: str = "act-1") -> ActionPlan:
    return ActionPlan(
        action_id=action_id,
        tool_id="channel.send",
        args={"text": "hi"},
        intent="Reply to customer",
        risk_hint=RiskTier.ORANGE_C,
    )


def test_enqueue_and_peek() -> None:
    q = HITLQueue()
    plan = _plan()
    q.enqueue(plan, reason="free-form outbound reply")
    items = q.pending()
    assert len(items) == 1
    assert items[0].plan.action_id == "act-1"
    assert items[0].reason == "free-form outbound reply"


def test_approve_removes_from_pending() -> None:
    q = HITLQueue()
    q.enqueue(_plan("a1"), reason="r")
    q.approve("a1", reviewer="human-1")
    assert q.pending() == []


def test_reject_removes_from_pending() -> None:
    q = HITLQueue()
    q.enqueue(_plan("a2"), reason="r")
    q.reject("a2", reviewer="human-2", note="inappropriate")
    assert q.pending() == []


def test_approve_unknown_raises() -> None:
    q = HITLQueue()
    with pytest.raises(KeyError):
        q.approve("nonexistent", reviewer="h")
