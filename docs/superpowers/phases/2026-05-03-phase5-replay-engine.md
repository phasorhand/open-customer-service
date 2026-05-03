# Phase 5 — Replay Engine · Close Note

**Date closed:** 2026-05-03
**Total tests:** 178 (138 from Phase 4 + 40 new in Phase 5)
**Status:** ✅ All tests pass, ruff clean, mypy strict clean

---

## What was built

The Replay Engine allows re-executing conversation traces with optional artifact overrides, producing structured diffs and verdicts to validate badcase fix proposals.

### New module: `src/opencs/replay/`

| File | Role |
|---|---|
| `types.py` | `ReplayMode`, `ReplayScope`, `Verdict`, `DivergenceKind`, `DivergencePoint`, `ReplayOverrides`, `ReplaySession`, `ReplayResult` |
| `trace_loader.py` | `TraceLoader` → reads L0 events, builds `Trace` (inbound messages, llm_cache, tool_cache) |
| `replaying_llm.py` | `ReplayingLLMClient` → serves cached LLM responses (STRICT) or calls real LLM (WHAT_IF/PARTIAL) |
| `replaying_tool.py` | `ReplayingToolExecutor` → serves cached tool results or re-runs real tool (WHAT_IF + override) |
| `read_only_channel.py` | `ReadOnlyChannelAdapter` → captures channel sends without dispatching |
| `differ.py` | `ReplayDiffer` → structural diff of two L0 event sequences → `DivergencePoint[]` + `Verdict` |
| `engine.py` | `ReplayEngine` → orchestrates full replay session end-to-end |
| `__init__.py` | Public exports |

### Modified files

| File | Change |
|---|---|
| `src/opencs/memory/l0_store.py` | Added `list_by_kinds()` method (filter events by multiple kinds) |
| `tests/agents/test_orchestrator_tool_dispatch.py` | Added L0 event stream integrity assertion |

---

## Replay modes

| Mode | LLM | Tools | Use case |
|---|---|---|---|
| STRICT | Cached (sequential) | Cached by action_id | Regression check: identical replay should produce identical output |
| PARTIAL | Real LLM (with overrides) | Cached | Test new prompt/model against frozen tool data |
| WHAT_IF | Real LLM (with overrides) | Cached unless in `tool_ids_to_rerun` | Full what-if: test fix proposal end-to-end |

---

## Verdict logic

| Condition | Verdict |
|---|---|
| No divergences, no badcase_event_index | `BADCASE_FIXED` |
| No divergences, badcase event unchanged | `BADCASE_REMAINS` |
| Previously-successful event now fails | `NEW_REGRESSION` |
| Divergences exist, badcase event changed | `BADCASE_FIXED` |
| All other cases | `INCONCLUSIVE` |

---

## Test breakdown (40 new tests)

| Suite | Count |
|---|---|
| `tests/replay/test_types.py` | 7 |
| `tests/replay/test_trace_loader.py` | 6 |
| `tests/replay/test_replaying_llm.py` | 7 |
| `tests/replay/test_replaying_tool.py` | 5 |
| `tests/replay/test_differ.py` | 6 |
| `tests/replay/test_engine.py` | 4 |
| `tests/test_e2e_replay.py` | 4 |
| `tests/agents/test_orchestrator_tool_dispatch.py` (new test) | 1 |

---

## Known deferrals (per spec §3.10.6)

- `llm_call` L0 events not yet auto-recorded by Orchestrator during live conversations — replay tests seed them manually → Phase 5.1 or Phase 6
- `SINGLE_TURN` scope → v1
- Batch replay / historical badcase regression suite → v1
- Verdict auto-evaluation via DeepEval → v1
- Memory L2 version rollback (`l2_version_id` override) → v1
- CLI (`opencs replay <trace_id>`) and API (`POST /replays`) entry points → Phase 6

---

## Hand-off contract for Phase 6 (Evolution layer)

Phase 6 consumes the Replay Engine via this interface:

```python
from opencs.replay import ReplayEngine, ReplaySession, ReplayMode, ReplayScope, ReplayOverrides

engine = ReplayEngine(
    l0=memory.l0,
    tool_registry=tool_registry,
    llm_fallback=llm_client,
)
result = await engine.replay(ReplaySession(
    source_conversation_id="conv-id",
    mode=ReplayMode.WHAT_IF,
    scope=ReplayScope.CONVERSATION,
    overrides=ReplayOverrides(
        prompt_override="...",
        tool_ids_to_rerun=["crm.get_order"],
    ),
))
# result.verdict: Verdict enum
# result.divergence_points: list[DivergencePoint]
# result.session_id, result.baseline_event_count, result.replay_event_count
```

**Requirement for Phase 6 PromotionGate:** Any fix proposal must attach a `ReplayResult` with `verdict != INCONCLUSIVE` before entering PromotionGate review.
