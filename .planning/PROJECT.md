# OpenCS

## What This Is

OpenCS is an open-source, self-hostable private-domain customer service AI platform. It gives enterprise WeChat (企微) customer service teams a fully auditable agent loop: incoming messages are handled by an Orchestrator + Worker architecture, CRM tools are called under a tiered action guard, and every decision that touches customers is logged, replayable, and evolvable through a HITL review panel.

## Core Value

A customer service agent that operators can actually trust — every action is auditable, every evolution is human-approved, and the whole system runs on your own infrastructure.

## Requirements

### Validated (MVP — shipped in v1.0)

- ✓ Channel Gateway: 企微客服 + WebChat adapters — Phase 1
- ✓ Orchestrator + CS Reply Worker + Approval Router Worker — Phase 2
- ✓ ActionGuard with tiered risk (Green/Yellow/Orange/Red) + ExecutionToken — Phase 2
- ✓ AuditLog (SQLite-backed, queryable) — Phase 2
- ✓ HITL queue (in-memory → persistent) — Phase 2
- ✓ Skills Repo: bundled skills + FTS5 retrieval — Phase 3
- ✓ Memory: L0/L1/L2 three-tier write model + FTS5 search — Phase 3
- ✓ ToolProvider: APIToolProvider + read-only CRM tool — Phase 4
- ✓ CRM manual config (schema JSON → operations exposure) — Phase 4
- ✓ Replay engine: What-if / Strict / Partial modes + verdict — Phase 5
- ✓ Evolution layer: Skill / Memory / CRM-Tool Proposal + Gate + ShadowRunner — Phase 6
- ✓ Admin REST API: proposals, audit-log, stats, CRM config — Phase 7a
- ✓ Admin Web UI (Next.js 14): HITL panel, audit log, replay, CRM wizard — Phase 7b
- ✓ Docker Compose one-command deployment (5 services) — Phase 7c

### Active

(Defined in v1.1 milestone)

### Out of Scope

- Multi-tenant SaaS — single-org self-hosted first; v2+
- 图片 OCR — deferred to v1.1
- UIToolProvider / MCPToolProvider — deferred to v1.1
- CRM auto-discovery (API-first + UI fallback) — deferred to v1.1
- Learned skill auto-sedimentation — deferred to v1.1
- Full 5-dimension Evolution (Prompt/Config + Signal-Loop) — deferred to v1.1
- Vector search (sqlite-vec / Qdrant) — deferred to v1.1
- Batch replay / DeepEval verdict — deferred to v1.1
- Feishu group bot — deferred to v1.1
- K8s Helm chart — deferred to v1.1

## Context

- **Language**: Python 3.12 (backend, uv), TypeScript/Next.js 14 (admin UI)
- **Storage**: SQLite (all stores — evolution.db, audit.db, memory.db); no Postgres in app layer
- **LLM**: LiteLLM abstraction (defaults to claude-sonnet-4-6)
- **Tracing**: Langfuse (self-hosted, optional)
- **Queue**: Redis (arq) in compose stack; in-process queue for dev
- **Testing**: pytest (293 passing), Vitest (React components)
- **Deploy**: Docker Compose (opencs-api:8000, web-ui:3000, langfuse:3001, postgres, redis)
- **Architecture pattern**: Orchestrator → Worker, ChannelAdapter, ToolProvider, Evolution Gate

## Constraints

- **OSS-First**: Every new module must have RESEARCH.md evaluating OSS options before implementation
- **License**: MIT/Apache-2.0/BSD preferred; GPL/AGPL prohibited; LGPL case-by-case
- **Self-hosted**: No mandatory cloud dependencies; all infra must run on bare Docker
- **Single-org**: No multi-tenancy in v1.x; schema must be forward-compatible (group_id reserved)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLite for all stores | Self-hosted simplicity, no Postgres app dep | ✓ Good |
| LiteLLM abstraction | Model-agnostic, easy swap | ✓ Good |
| Next.js standalone output | Docker-friendly, no Node server process | ✓ Good |
| uv for Python packaging | Fast installs in CI/Docker | ✓ Good |
| copy src/ before uv install | hatchling needs source present at build time | ✓ Good |
| Langfuse on port 3002 locally | 3001 often occupied; override in compose | ✓ Good |

---
*Last updated: 2026-05-04 after MVP (v1.0) complete — all Phases 1–7c shipped*
