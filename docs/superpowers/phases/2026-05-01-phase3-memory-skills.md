# Phase 3 Memory + Skills — close note

## Delivered
- `L0RawEventStore` — append-only SQLite event log (source of truth for Replay, Phase 5)
- `L1SessionStore` — ephemeral in-memory session state (turn counter, last intent)
- `L2MemoryStore` — long-term memory with FTS5 keyword search; versioned writes (CoW)
- `MemoryStore` facade — `record_inbound()` + `load_context()` + `write_l2()`
- `SkillRepo` — loads bundled SKILL.md files, keyword-matches against customer message
- Bundled skills: `greeting` + `refund_policy` (SKILL.md format with YAML frontmatter)
- `CSReplyWorker` enriched with memory summary + skill guidelines in system prompt
- `Orchestrator` wired with optional `MemoryStore` + `SkillRepo`; `main.py` updated
- E2E test: inbound message → skill keyword match → LLM prompt enriched → L0 event logged

## Tests
`uv run pytest -v` — 108 tests passing.

## Known deferrals (intentional)
- Vector search (sqlite-vec / Qdrant) → v1
- `learned` skill auto-sedimentation → v1
- Memory Consolidation background process (L0→L2 distillation) → Phase 5/6
- PII redaction before LLM → Phase 7
- L2 writes through Evolution Proposal gate → Phase 6 (here we write directly)
- Social Perception session state machine (`transitions`) → future Social Perception module
- Memory L2 version snapshot for Replay → Phase 5

## Hand-off contract for Phase 4 (ToolProvider / CRM API Tool)
- `WorkerInput.session_context` is fully populated by Orchestrator before worker dispatch
- `MemoryStore.write_l2()` is the API for workers to persist new long-term facts
- `L0RawEventStore` schema is stable; Phase 5 Replay reads it directly
- `CSReplyWorker` can be extended to call CRM tools and append results to the user message
