# OpenCS Admin Web UI

Next.js 14 admin console for the OpenCS customer-service agent.

## Prerequisites
- Node.js 20+
- Running `opencs-api` on port 8000 (see Phase 7a)

## Development

```bash
cd web-ui
npm install
OPENCS_API_BASE=http://localhost:8000 npm run dev
```

Open http://localhost:3000.

## Pages
- `/` — Dashboard (pending count, recent activity)
- `/proposals` — HITL approval panel with filters
- `/proposals/:id` — Proposal detail + approve/reject
- `/audit-log` — Paginated audit log with actor filter
- `/replays` — Configure + trigger a replay; view verdict
- `/crm` — Multi-step wizard to configure CRM integration

## Testing

```bash
npm test          # Run vitest once
npm run typecheck # tsc --noEmit
npm run build     # production build smoke test
```

## Environment
- `OPENCS_API_BASE` — backend base URL. Defaults to `http://opencs-api:8000` for Docker.

## Langfuse trace deep-links
Set `langfuse_host` in localStorage (via DevTools → Application → Local Storage) to your
Langfuse host (e.g., `http://localhost:3001`). Proposal detail pages will then render
clickable trace links for proposals with a `trace_id`.
