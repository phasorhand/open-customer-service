# Phase 6 — Dual-Track Evolution Layer · Close Note

**Date closed:** 2026-05-03
**Total tests:** 249 (178 from Phase 5 + 71 new in Phase 6)
**Status:** ✅ All tests pass, ruff clean, mypy strict clean

---

## What was built

The Dual-Track Evolution layer: all writes to Skill files, L2 Memory, and ToolRegistry flow through a Proposal → EvolutionGate → Handler pipeline. ShadowRunner validates fix proposals via ReplayEngine before gate evaluation. HITL queue supports human review for high-risk or PII-sensitive changes.

### New module: `src/opencs/evolution/`

| File | Role |
|---|---|
| `RESEARCH.md` | OSS gate documentation (required by CLAUDE.md) |
| `types.py` | `EvolutionDimension`, `ProposalAction`, `ProposalStatus`, `GateDecision`, `Proposal` |
| `proposal_store.py` | `ProposalStore` — SQLite persistence for proposals |
| `gate.py` | `EvolutionGate` — dimension-specific policy (§4.3) |
| `handlers/skill.py` | `SkillProposalHandler` — write/remove .md files |
| `handlers/memory.py` | `MemoryProposalHandler` — writes to L2MemoryStore |
| `handlers/crm_tool.py` | `CRMToolProposalHandler` — register/deregister via ToolRegistry |
| `shadow_runner.py` | `ShadowRunner` — WhatIf replay validation before PromotionGate |
| `hitl_queue.py` | `EvolutionHITLQueue` — in-memory HITL approval queue |
| `__init__.py` | Public re-exports (14 symbols) |

### New file: `src/opencs/gateway/routes_replay.py`

| Endpoint | Status | Description |
|---|---|---|
| `POST /replays` | 200 | Execute replay session, returns verdict + metrics |
| `POST /replays` | 503 | When no `replay_engine` configured |

### Modified files

| File | Change |
|---|---|
| `src/opencs/gateway/app.py` | Added `replay_engine=None` param, mounts `/replays` router |
| `src/opencs/tools/registry.py` | Added `deregister(tool_id)` method (idempotent) |

---

## EvolutionGate policy (§4.3)

| Dimension | AUTO_PROMOTE | HITL_PENDING |
|---|---|---|
| **Skill** | low/medium risk, no orange/red action | high/critical risk OR involves_orange_red_action |
| **Memory** | non-PII key, no pii_detected evidence | PII key match OR pii_detected=True OR high/critical risk |
| **CRM Tool** | ≥3 dry_run successes, no first_integration, no write | first_integration OR involves_write OR <3 dry_runs |

---

## ShadowRunner behavior

| Condition | blocks_gate |
|---|---|
| No `badcase_conversation_id` in evidence | `False` (replay skipped) |
| Replay verdict = `BADCASE_FIXED` | `False` |
| Replay verdict = `BADCASE_REMAINS` | `False` |
| Replay verdict = `NEW_REGRESSION` | `False` |
| Replay verdict = `INCONCLUSIVE` | `True` |

---

## Test breakdown (71 new tests)

| Suite | Count |
|---|---|
| `tests/evolution/test_types.py` | 7 |
| `tests/evolution/test_proposal_store.py` | 7 |
| `tests/evolution/test_gate.py` | 14 |
| `tests/evolution/test_skill_handler.py` | 6 |
| `tests/evolution/test_memory_handler.py` | 7 |
| `tests/evolution/test_crm_tool_handler.py` | 8 |
| `tests/evolution/test_shadow_runner.py` | 6 |
| `tests/evolution/test_hitl_queue.py` | 8 |
| `tests/gateway/test_routes_replay.py` | 5 |
| `tests/test_e2e_evolution.py` | 3 |

---

## Known deferrals (per spec §7.1)

- arq + Redis async Proposal queue → v1 (MVP uses in-process synchronous pipeline)
- Langfuse HITL queue persistence → Phase 7 (current impl is in-memory)
- Admin Web UI: HITL panel + AuditLog viewer + Badcase repair panel → Phase 7
- MemoryStore.write_l2() routing through MemoryProposalHandler in live agent flows → Phase 7
- Full 5-dimension Evolution (Prompt/Config + Signal-Loop) → v1 per spec §4.3
- Evolution Dashboard → Phase 7 / v1
- Docker Compose one-click deploy → Phase 7
- ProposalStore migration to Postgres → v1 (currently SQLite, interface is forward-compatible)
- Rollback mechanism: record previous_version on promotion → Phase 7
- llm_call L0 events auto-recorded by Orchestrator during live conversations → Phase 7

---

## Hand-off contract for Phase 7 (Admin Web UI + Docker Compose)

Phase 7 consumes the Evolution layer via this interface:

```python
from opencs.evolution import (
    EvolutionGate,
    EvolutionHITLQueue,
    Proposal,
    ProposalStore,
    ShadowRunner,
    SkillProposalHandler,
    MemoryProposalHandler,
    CRMToolProposalHandler,
)

# --- Proposal lifecycle ---
store = ProposalStore(db_path="evolution.db")
store.save(proposal)
store.update_status(proposal.id, ProposalStatus.SHADOW_RUNNING)

# --- Shadow validation ---
runner = ShadowRunner(engine=replay_engine)
shadow_result = await runner.run(proposal)
if shadow_result.blocks_gate:
    store.update_status(proposal.id, ProposalStatus.REJECTED)
    return

# --- Gate evaluation ---
gate = EvolutionGate(audit_log=audit_log)
decision = gate.evaluate(proposal)

if decision == GateDecision.HITL_PENDING:
    hitl_queue.enqueue(proposal, reason="...")
    store.update_status(proposal.id, ProposalStatus.HITL_PENDING)
elif decision == GateDecision.AUTO_PROMOTE:
    handler.apply(proposal)
    store.update_gate_decision(proposal.id, gate_decision=decision, status=ProposalStatus.AUTO_PROMOTED)

# --- HITL approval (Admin UI calls this) ---
item = hitl_queue.approve(proposal_id, reviewer="admin")
handler.apply(item.proposal)
store.update_gate_decision(proposal_id, gate_decision=GateDecision.HITL_PENDING,
                           status=ProposalStatus.HITL_APPROVED, reviewer="admin")
```

### POST /replays API

```
POST /replays
{
  "source_conversation_id": "conv-id",
  "mode": "what_if",           // what_if | strict | partial
  "scope": "conversation",     // conversation | single_turn
  "overrides": {
    "prompt_override": "...",
    "skill_override": "...",
    "model_override": "..."
  }
}

Response 200:
{
  "session_id": "...",
  "verdict": "badcase_fixed",
  "divergence_count": 0,
  "baseline_event_count": 4,
  "replay_event_count": 4
}
```

**Phase 7 requirements:**
1. Admin Web UI must provide HITL approval panel → calls `hitl_queue.approve()`/`.reject()`
2. Replace in-memory `EvolutionHITLQueue` with Langfuse-backed persistent queue
3. Wire `MemoryProposalHandler` into live agent `write_l2()` path
4. Docker Compose includes SQLite volume mount for `evolution.db` + `audit.db`
