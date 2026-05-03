# Phase 7 — Admin Web UI + Docker Compose: Design Spec

> **Date:** 2026-05-03
> **Phase:** 7 (final MVP phase)
> **Prerequisite:** Phase 6 (Evolution Layer) complete
> **Approach:** API-first — Backend endpoints → Frontend pages → Docker packaging

---

## § 1. Scope

Phase 7 delivers:

1. **Admin REST API** — FastAPI endpoints for HITL approval, audit log, replay management, CRM config
2. **Next.js Frontend** — 4 pages: HITL Approval Panel, AuditLog Viewer, Badcase Repair Panel, CRM Config Wizard
3. **Langfuse Integration** — Self-hosted Langfuse for LLM tracing + proposal context linking (hybrid mode)
4. **Docker Compose** — Consolidated MVP deployment (opencs-api, web-ui, langfuse, redis)

### Phase 6 Hand-off Requirements (all addressed)

1. Admin Web UI provides HITL approval panel → calls `hitl_queue.approve()`/`.reject()` ✓
2. Replace in-memory `EvolutionHITLQueue` with persistent queue (hybrid: SQLite + Langfuse trace linking) ✓
3. Wire `MemoryProposalHandler` into live agent `write_l2()` path ✓
4. Docker Compose includes SQLite volume mount for `evolution.db` + `audit.db` ✓

---

## § 2. Admin REST API

All admin endpoints are mounted under `/admin` on the existing FastAPI gateway.

### 2.1 Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/admin/proposals` | GET | List proposals (filterable by status, dimension, paginated) |
| `/admin/proposals/{id}` | GET | Proposal detail (includes replay verdict, Langfuse trace_id) |
| `/admin/proposals/{id}/approve` | POST | HITL approve (body: `{reviewer: string}`) |
| `/admin/proposals/{id}/reject` | POST | HITL reject (body: `{reviewer: string, note?: string}`) |
| `/admin/audit-log` | GET | Paginated audit log (filterable by actor, action, timerange) |
| `/admin/replays` | POST | Trigger a replay (same schema as existing POST /replays) |
| `/admin/replays/{session_id}` | GET | Get replay session results |
| `/admin/crm/config` | GET | Read current CRM configuration |
| `/admin/crm/config` | PUT | Write CRM configuration |
| `/admin/crm/validate` | POST | Validate CRM schema/connection |
| `/admin/stats` | GET | Dashboard stats (pending count, recent decisions, proposal breakdown) |

### 2.2 Authentication

MVP: No auth (single-tenant, trusted network). The Docker Compose network isolates admin endpoints. A `X-Admin-Token` header check can be added as a follow-up (env var based).

### 2.3 Data Sources

- **ProposalStore** (SQLite `evolution.db`) — proposals, status, gate decisions
- **AuditLog** (SQLite `audit.db`) — append-only decision log
- **ReplayEngine** — existing Phase 5 module, invoked for badcase repair
- **Langfuse SDK** — trace queries for proposal context
- **CRM config** — new `crm_config` table in `evolution.db`

---

## § 3. Langfuse Integration (Hybrid Mode)

### 3.1 Architecture

```
SQLite ProposalStore = Source of truth for proposal state (pending/approved/rejected)
Langfuse = LLM tracing + context retrieval (not the queue)
```

Each proposal stores a `trace_id` field. When admin reviews a proposal, the UI can deep-link to Langfuse's trace view showing the full conversation that generated it.

### 3.2 Tracing Integration

- Instrument the orchestrator and agent LLM calls with Langfuse's Python SDK (`@observe` decorator or context manager)
- Each conversation gets a trace; each LLM call is a span within
- When Evolution generates a Proposal, the current trace_id is stored on the Proposal record

### 3.3 Replay Trace Linking

- Replay sessions create their own Langfuse trace
- The replay trace's metadata includes `source_trace_id` (the original conversation)
- Admin UI shows both traces side-by-side for before/after comparison

### 3.4 Persistent HITL Queue

Replace in-memory `EvolutionHITLQueue` with `PersistentHITLQueue`:
- Same interface: `enqueue()`, `pending()`, `approve()`, `reject()`
- Backed by ProposalStore (SQLite) — status field is the queue state
- No separate queue table; the proposal's `status` field (PENDING_HITL → APPROVED/REJECTED) IS the queue

### 3.5 Self-hosted Langfuse

- Langfuse Docker image in compose stack
- Langfuse uses its own PostgreSQL (bundled via Langfuse's docker setup or a small `postgres:16-alpine` sidecar)
- Connection: `LANGFUSE_HOST=http://langfuse:3001` (internal Docker network)

---

## § 4. Next.js Frontend

### 4.1 Tech Stack

- **Framework:** Next.js 14+ (App Router, TypeScript)
- **UI:** shadcn/ui (Tailwind CSS based)
- **Data fetching:** TanStack Query v5
- **Forms:** react-hook-form + zod validation
- **API proxy:** Next.js rewrites (`/api/*` → `opencs-api:8000/admin/*`)

### 4.2 Directory Structure

```
web-ui/
├── src/
│   ├── app/
│   │   ├── layout.tsx              — Admin shell (sidebar nav + header)
│   │   ├── page.tsx                — Dashboard (stats cards, recent activity)
│   │   ├── proposals/
│   │   │   ├── page.tsx            — HITL Approval Panel (table + actions)
│   │   │   └── [id]/page.tsx       — Proposal detail (verdict, trace link)
│   │   ├── audit-log/
│   │   │   └── page.tsx            — Paginated log viewer
│   │   ├── replays/
│   │   │   ├── page.tsx            — Badcase Repair (configure + trigger)
│   │   │   └── [id]/page.tsx       — Replay results (diff, verdict)
│   │   └── crm/
│   │       └── page.tsx            — CRM Config Wizard (multi-step)
│   ├── components/
│   │   ├── ui/                     — shadcn/ui primitives
│   │   ├── proposals-table.tsx
│   │   ├── audit-log-table.tsx
│   │   ├── replay-config-form.tsx
│   │   ├── crm-wizard-steps.tsx
│   │   └── sidebar-nav.tsx
│   ├── lib/
│   │   ├── api.ts                  — TanStack Query hooks
│   │   ├── types.ts                — TypeScript types (mirror pydantic models)
│   │   └── utils.ts
│   └── ...
├── package.json
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

### 4.3 Page Descriptions

**Dashboard (`/`)**
- Cards: pending proposals count, total approved today, active replay sessions
- Recent activity feed (last 10 audit log entries)
- Quick actions: "Review pending proposals", "Run replay"

**HITL Approval Panel (`/proposals`)**
- Data table with columns: ID, Dimension (Skill/Memory/Tool), Summary, Status, Created, Actions
- Filter by status (pending/approved/rejected) and dimension
- Approve/Reject buttons inline with confirmation dialog
- Click row → detail page with full proposal JSON, replay verdict, link to Langfuse trace

**AuditLog Viewer (`/audit-log`)**
- Paginated table: Timestamp, Actor, Action, Target, Details
- Filter by actor, action type, date range
- Expandable rows for full detail JSON

**Badcase Repair Panel (`/replays`)**
- Step 1: Enter/select source conversation ID
- Step 2: Configure replay mode (what_if/strict/partial), scope, overrides
- Step 3: Submit → show progress indicator
- Step 4: Display results (verdict, divergence_count, structured diff)
- Step 5: If badcase_fixed → button "Create Evolution Proposal"

**CRM Config Wizard (`/crm`)**
- Step 1: Enter CRM base URL
- Step 2: Upload OpenAPI/Swagger JSON or paste schema
- Step 3: Validate connection (POST /admin/crm/validate)
- Step 4: Review detected operations, select which to expose as tools
- Step 5: Save (PUT /admin/crm/config) → confirmation

---

## § 5. Docker Compose

### 5.1 Service Topology (Consolidated MVP)

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| `opencs-api` | `Dockerfile.api` (Python 3.12) | 8000 | FastAPI: gateway + orchestrator + evolution + admin API |
| `web-ui` | `Dockerfile.web` (Node 20) | 3000 | Next.js admin frontend |
| `langfuse` | `langfuse/langfuse:2` | 3001 | LLM tracing + annotation |
| `langfuse-db` | `postgres:16-alpine` | (internal) | Langfuse's database |
| `redis` | `redis:7-alpine` | 6379 | arq task queue + caching |

### 5.2 Volumes

- `opencs-data:/data` → mapped into opencs-api; contains `evolution.db`, `audit.db`, `memory.db`
- `langfuse-pgdata` → Langfuse's Postgres data
- `redis-data` → Redis persistence (optional, AOF)

### 5.3 Network

Single Docker network `opencs-net`. All inter-service communication uses Docker DNS (e.g., `http://opencs-api:8000`).

### 5.4 Environment Variables

```yaml
# .env.example
# LLM
LITELLM_MODEL=anthropic/claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...

# Langfuse
LANGFUSE_HOST=http://langfuse:3001
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Redis
REDIS_URL=redis://redis:6379

# WeChat (optional)
WECOM_CORP_ID=
WECOM_TOKEN=
WECOM_ENCODING_AES_KEY=

# Data
DATA_DIR=/data
```

### 5.5 Dockerfiles

**Dockerfile.api:**
- Base: `python:3.12-slim`
- Install deps from `pyproject.toml`
- Copy `src/opencs/`
- CMD: `uvicorn opencs.main:app --host 0.0.0.0 --port 8000`

**Dockerfile.web:**
- Base: `node:20-alpine`
- Install deps, build Next.js (`npm run build`)
- CMD: `npm start` (production server on port 3000)

### 5.6 Startup & Health

- `opencs-api` depends_on: redis (healthy), langfuse (healthy)
- `web-ui` depends_on: opencs-api (healthy)
- Health checks: `/health` on opencs-api, Next.js built-in, Langfuse `/api/public/health`

---

## § 6. Backend Changes Required

### 6.1 New Files

```
src/opencs/gateway/routes_admin.py     — Admin API router (all /admin/* endpoints)
src/opencs/evolution/persistent_queue.py — PersistentHITLQueue (replaces in-memory)
src/opencs/tracing/langfuse_client.py   — Langfuse SDK wrapper (init, trace helpers)
src/opencs/gateway/admin_schemas.py     — Pydantic request/response models for admin API
```

### 6.2 Modified Files

```
src/opencs/gateway/app.py              — mount admin router
src/opencs/evolution/hitl_queue.py     — deprecate in-memory queue (keep interface)
src/opencs/evolution/gate.py           — inject trace_id into proposals
src/opencs/agents/orchestrator.py      — add Langfuse tracing decorator
```

### 6.3 MemoryProposalHandler Wiring

The Phase 6 hand-off requires wiring `MemoryProposalHandler` into the live agent `write_l2()` path. This means:
- When agent calls `memory_store.write_l2(...)`, it goes through Evolution:
  1. Create a Proposal (dimension=MEMORY, action=CREATE)
  2. EvolutionGate evaluates → auto-promote or HITL
  3. If auto: MemoryProposalHandler.apply() writes to L2
  4. If HITL: queued for admin approval

---

## § 7. Testing Strategy

- **Backend:** pytest-asyncio for admin API endpoints (httpx AsyncClient)
- **Frontend:** Vitest + React Testing Library for component tests
- **E2E:** One integration test: create proposal → approve via admin API → verify state change
- **Docker:** `docker compose up --build` smoke test (health checks pass)

---

## § 8. Out of Scope (deferred to v1)

- Multi-tenant auth / RBAC
- Full Evolution Dashboard (Langfuse's built-in UI covers basics)
- Learned skill auto-creation
- K8s Helm chart
- UIToolProvider / MCPToolProvider
