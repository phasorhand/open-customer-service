from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ReplayMode(StrEnum):
    STRICT = "strict"
    PARTIAL = "partial"
    WHAT_IF = "what_if"


class ReplayScope(StrEnum):
    CONVERSATION = "conversation"
    SINGLE_TURN = "single_turn"


class Verdict(StrEnum):
    BADCASE_FIXED = "badcase_fixed"
    BADCASE_REMAINS = "badcase_remains"
    NEW_REGRESSION = "new_regression"
    INCONCLUSIVE = "inconclusive"


class DivergenceKind(StrEnum):
    ACTION_CHANGED = "action_changed"
    CONTENT_CHANGED = "content_changed"
    TOOL_MISSING = "tool_missing"
    TOOL_ADDED = "tool_added"
    LLM_OUTPUT_CHANGED = "llm_output_changed"


@dataclass(frozen=True)
class DivergencePoint:
    step_index: int
    kind: DivergenceKind
    baseline_summary: str
    replay_summary: str


@dataclass(frozen=True)
class ReplayOverrides:
    prompt_override: str | None = None
    skill_override: str | None = None
    tool_ids_to_rerun: list[str] = field(default_factory=list)
    model_override: str | None = None
    l2_version_id: str | None = None


@dataclass(frozen=True)
class ReplaySession:
    source_conversation_id: str
    mode: ReplayMode
    scope: ReplayScope
    overrides: ReplayOverrides = field(default_factory=ReplayOverrides)
    turn_index: int | None = None  # only for SINGLE_TURN scope


@dataclass(frozen=True)
class ReplayResult:
    session_id: str
    verdict: Verdict
    divergence_points: list[DivergencePoint]
    replay_event_count: int
    baseline_event_count: int
