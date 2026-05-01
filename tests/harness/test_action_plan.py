import pytest
from pydantic import ValidationError

from opencs.harness.action_plan import ActionPlan, RiskTier


def test_action_plan_round_trips() -> None:
    plan = ActionPlan(
        action_id="act-abc",
        tool_id="crm.read_customer",
        args={"customer_id": "c1"},
        intent="Look up customer profile to personalise the reply",
        risk_hint=RiskTier.GREEN,
    )
    assert plan.action_id == "act-abc"
    assert plan.tool_id == "crm.read_customer"
    assert plan.risk_hint == RiskTier.GREEN


def test_action_plan_rejects_empty_intent() -> None:
    with pytest.raises(ValidationError):
        ActionPlan(
            action_id="a",
            tool_id="t",
            args={},
            intent="",
            risk_hint=RiskTier.GREEN,
        )


def test_action_plan_immutable() -> None:
    plan = ActionPlan(
        action_id="a",
        tool_id="t",
        args={},
        intent="test",
        risk_hint=RiskTier.GREEN,
    )
    with pytest.raises((AttributeError, ValidationError)):
        plan.tool_id = "other"  # type: ignore[misc]


def test_risk_tier_ordering() -> None:
    tiers = [RiskTier.GREEN, RiskTier.YELLOW, RiskTier.ORANGE_A,
             RiskTier.ORANGE_B, RiskTier.ORANGE_C, RiskTier.RED]
    assert tiers[0] < tiers[-1]


def test_channel_reply_action_plan() -> None:
    plan = ActionPlan(
        action_id="reply-001",
        tool_id="channel.send",
        args={"conversation_id": "c1", "text": "Hello!"},
        intent="Send reply to customer",
        risk_hint=RiskTier.ORANGE_C,
    )
    assert plan.risk_hint == RiskTier.ORANGE_C
