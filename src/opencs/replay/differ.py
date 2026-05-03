from __future__ import annotations

import json
from dataclasses import dataclass

from opencs.memory.l0_store import L0Event
from opencs.replay.types import DivergenceKind, DivergencePoint, Verdict


@dataclass
class DiffResult:
    divergence_points: list[DivergencePoint]
    verdict: Verdict


class ReplayDiffer:
    """Compares baseline and replay L0 event sequences to produce structured diff + verdict.

    Verdict logic:
    - No divergences → BADCASE_FIXED (the replay produced same output, which means
      if overrides were applied, the fix holds).
    - Divergences exist but the badcase event is unchanged → BADCASE_REMAINS.
    - A previously-successful event now fails → NEW_REGRESSION.
    - Otherwise → INCONCLUSIVE.
    """

    def __init__(self, *, badcase_event_index: int | None = None) -> None:
        self._badcase_idx = badcase_event_index

    def diff(self, *, baseline: list[L0Event], replay: list[L0Event]) -> DiffResult:
        divergences: list[DivergencePoint] = []
        max_len = max(len(baseline), len(replay)) if (baseline or replay) else 0

        for i in range(max_len):
            b = baseline[i] if i < len(baseline) else None
            r = replay[i] if i < len(replay) else None

            _tool_kinds = ("tool_call", "tool_result")
            if b is None and r is not None:
                divergences.append(DivergencePoint(
                    step_index=i,
                    kind=DivergenceKind.TOOL_ADDED if r.kind in _tool_kinds
                    else DivergenceKind.CONTENT_CHANGED,
                    baseline_summary="<missing>",
                    replay_summary=f"{r.kind}: {_summarize(r.payload)}",
                ))
            elif r is None and b is not None:
                divergences.append(DivergencePoint(
                    step_index=i,
                    kind=DivergenceKind.TOOL_MISSING if b.kind in _tool_kinds
                    else DivergenceKind.CONTENT_CHANGED,
                    baseline_summary=f"{b.kind}: {_summarize(b.payload)}",
                    replay_summary="<missing>",
                ))
            elif b is not None and r is not None:
                if b.kind != r.kind or _canon(b.payload) != _canon(r.payload):
                    kind = _classify_divergence(b, r)
                    divergences.append(DivergencePoint(
                        step_index=i,
                        kind=kind,
                        baseline_summary=f"{b.kind}: {_summarize(b.payload)}",
                        replay_summary=f"{r.kind}: {_summarize(r.payload)}",
                    ))

        verdict = self._determine_verdict(baseline, replay, divergences)
        return DiffResult(divergence_points=divergences, verdict=verdict)

    def _determine_verdict(
        self,
        baseline: list[L0Event],
        replay: list[L0Event],
        divergences: list[DivergencePoint],
    ) -> Verdict:
        if not divergences:
            if self._badcase_idx is not None:
                return Verdict.BADCASE_REMAINS
            return Verdict.BADCASE_FIXED

        has_new_failure = any(
            self._is_new_failure(baseline, replay, dp) for dp in divergences
        )
        if has_new_failure:
            return Verdict.NEW_REGRESSION

        if self._badcase_idx is not None:
            badcase_unchanged = not any(
                dp.step_index == self._badcase_idx for dp in divergences
            )
            if badcase_unchanged:
                return Verdict.BADCASE_REMAINS

        return Verdict.BADCASE_FIXED

    def _is_new_failure(
        self, baseline: list[L0Event], replay: list[L0Event], dp: DivergencePoint
    ) -> bool:
        i = dp.step_index
        b = baseline[i] if i < len(baseline) else None
        r = replay[i] if i < len(replay) else None
        if b and r and b.kind == "tool_result" and r.kind == "tool_result":
            was_ok = b.payload.get("success") is True
            now_fail = r.payload.get("success") is not True
            return was_ok and now_fail
        return False


def _canon(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def _summarize(payload: dict[str, object]) -> str:
    s = json.dumps(payload, ensure_ascii=False)
    return s[:120] + "..." if len(s) > 120 else s


def _classify_divergence(b: L0Event, r: L0Event) -> DivergenceKind:
    if b.kind != r.kind:
        if r.kind in ("tool_call", "tool_result"):
            return DivergenceKind.TOOL_ADDED
        if b.kind in ("tool_call", "tool_result"):
            return DivergenceKind.TOOL_MISSING
    if b.kind == "llm_call" or r.kind == "llm_call":
        return DivergenceKind.LLM_OUTPUT_CHANGED
    return DivergenceKind.CONTENT_CHANGED
