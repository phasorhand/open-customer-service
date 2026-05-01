from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field


class RiskTier(IntEnum):
    GREEN = 0      # read-only → auto-execute
    YELLOW = 1     # low-risk write → auto + post-audit
    ORANGE_A = 2   # template reply → auto + rate-limit + post-audit
    ORANGE_B = 3   # medium-risk write → auto + rate-limit + async review
    ORANGE_C = 4   # free-form outbound text → sync HITL (MVP default)
    RED = 5        # high-risk → sync HITL always


class ActionPlan(BaseModel):
    """Produced by Worker agents; consumed by ActionGuard."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action_id: str
    tool_id: str
    args: dict[str, object]
    intent: str = Field(min_length=1)
    risk_hint: RiskTier
