from opencs.replay.types import (
    DivergenceKind,
    DivergencePoint,
    ReplayMode,
    ReplayOverrides,
    ReplayResult,
    ReplayScope,
    ReplaySession,
    Verdict,
)


def test_replay_mode_values() -> None:
    assert ReplayMode.STRICT == "strict"
    assert ReplayMode.PARTIAL == "partial"
    assert ReplayMode.WHAT_IF == "what_if"


def test_replay_scope_values() -> None:
    assert ReplayScope.CONVERSATION == "conversation"
    assert ReplayScope.SINGLE_TURN == "single_turn"


def test_verdict_values() -> None:
    assert Verdict.BADCASE_FIXED == "badcase_fixed"
    assert Verdict.BADCASE_REMAINS == "badcase_remains"
    assert Verdict.NEW_REGRESSION == "new_regression"
    assert Verdict.INCONCLUSIVE == "inconclusive"


def test_replay_overrides_defaults() -> None:
    o = ReplayOverrides()
    assert o.prompt_override is None
    assert o.skill_override is None
    assert o.tool_ids_to_rerun == []
    assert o.model_override is None
    assert o.l2_version_id is None


def test_replay_session_construction() -> None:
    session = ReplaySession(
        source_conversation_id="conv-1",
        mode=ReplayMode.WHAT_IF,
        scope=ReplayScope.CONVERSATION,
        overrides=ReplayOverrides(prompt_override="You are a stricter agent."),
    )
    assert session.source_conversation_id == "conv-1"
    assert session.mode == ReplayMode.WHAT_IF
    assert session.overrides.prompt_override == "You are a stricter agent."


def test_divergence_point_construction() -> None:
    dp = DivergencePoint(
        step_index=3,
        kind=DivergenceKind.CONTENT_CHANGED,
        baseline_summary="reply: Hello!",
        replay_summary="reply: Hi there!",
    )
    assert dp.step_index == 3
    assert dp.kind == DivergenceKind.CONTENT_CHANGED


def test_replay_result_construction() -> None:
    result = ReplayResult(
        session_id="sess-1",
        verdict=Verdict.BADCASE_FIXED,
        divergence_points=[],
        replay_event_count=5,
        baseline_event_count=5,
    )
    assert result.verdict == Verdict.BADCASE_FIXED
    assert result.divergence_points == []
