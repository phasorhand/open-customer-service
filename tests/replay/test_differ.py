from datetime import UTC, datetime

from opencs.memory.l0_store import L0Event
from opencs.replay.differ import ReplayDiffer
from opencs.replay.types import DivergenceKind, Verdict


def _event(kind: str, payload: dict, ts_sec: int = 0) -> L0Event:
    return L0Event(
        conversation_id="conv-1",
        kind=kind,
        payload=payload,
        ts=datetime(2026, 5, 1, 10, 0, ts_sec, tzinfo=UTC),
    )


def test_identical_traces_produce_no_divergences() -> None:
    baseline = [
        _event("inbound_message", {"text": "hello"}, 0),
        _event("tool_call", {"tool_id": "crm.get_order", "args": {"order_id": "ord-001"}}, 1),
        _event("tool_result", {"tool_id": "crm.get_order", "success": True,
                               "data": {"status": "shipped"}}, 2),
    ]
    replay = list(baseline)
    differ = ReplayDiffer()
    result = differ.diff(baseline=baseline, replay=replay)
    assert result.divergence_points == []
    assert result.verdict == Verdict.BADCASE_FIXED  # no divergence → fix holds


def test_content_changed_detected() -> None:
    baseline = [
        _event("inbound_message", {"text": "hello"}, 0),
        _event("tool_result", {"tool_id": "crm.get_order", "success": True,
                               "data": {"status": "shipped"}}, 1),
    ]
    replay = [
        _event("inbound_message", {"text": "hello"}, 0),
        _event("tool_result", {"tool_id": "crm.get_order", "success": True,
                               "data": {"status": "delivered"}}, 1),
    ]
    differ = ReplayDiffer()
    result = differ.diff(baseline=baseline, replay=replay)
    assert len(result.divergence_points) == 1
    assert result.divergence_points[0].kind == DivergenceKind.CONTENT_CHANGED
    assert result.divergence_points[0].step_index == 1


def test_tool_added_detected() -> None:
    baseline = [
        _event("inbound_message", {"text": "hello"}, 0),
    ]
    replay = [
        _event("inbound_message", {"text": "hello"}, 0),
        _event("tool_call", {"tool_id": "crm.get_order", "args": {}}, 1),
    ]
    differ = ReplayDiffer()
    result = differ.diff(baseline=baseline, replay=replay)
    assert any(dp.kind == DivergenceKind.TOOL_ADDED for dp in result.divergence_points)


def test_tool_missing_detected() -> None:
    baseline = [
        _event("inbound_message", {"text": "hello"}, 0),
        _event("tool_call", {"tool_id": "crm.get_order", "args": {}}, 1),
    ]
    replay = [
        _event("inbound_message", {"text": "hello"}, 0),
    ]
    differ = ReplayDiffer()
    result = differ.diff(baseline=baseline, replay=replay)
    assert any(dp.kind == DivergenceKind.TOOL_MISSING for dp in result.divergence_points)


def test_badcase_remains_when_same_error() -> None:
    baseline = [
        _event("tool_result", {"tool_id": "t", "success": False, "data": {},
                               "error": "HTTP 500"}, 0),
    ]
    replay = [
        _event("tool_result", {"tool_id": "t", "success": False, "data": {},
                               "error": "HTTP 500"}, 0),
    ]
    differ = ReplayDiffer(badcase_event_index=0)
    result = differ.diff(baseline=baseline, replay=replay)
    assert result.verdict == Verdict.BADCASE_REMAINS


def test_new_regression_when_new_failure_introduced() -> None:
    baseline = [
        _event("tool_result", {"tool_id": "t", "success": True, "data": {"ok": True}}, 0),
    ]
    replay = [
        _event("tool_result", {"tool_id": "t", "success": False, "data": {}, "error": "broke"}, 0),
    ]
    differ = ReplayDiffer()
    result = differ.diff(baseline=baseline, replay=replay)
    assert result.verdict == Verdict.NEW_REGRESSION
