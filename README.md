# OpenCS

Open-source, self-hosted private-domain customer-service AI platform.

See `docs/superpowers/specs/2026-04-30-open-cs-mvp-architecture.md` for the full architecture.

## Dev quickstart

```bash
uv sync --all-groups
uv run pytest
uv run uvicorn opencs.gateway.app:create_default_app --factory --reload
```

## Run locally with Docker

**Prerequisites:** Docker 24+ with Compose v2, ~4GB free RAM.

```bash
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY. Optionally set LANGFUSE_* keys after first-run sign-up.
docker compose up -d --build
./scripts/docker-smoke-test.sh
```

Open the apps:
- Admin UI: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Langfuse: http://localhost:3001 (first user becomes admin; create a project, paste keys back into `.env`, then `docker compose up -d opencs-api`)

Data persists in Docker named volumes:
- `opencs-data` — SQLite files (`evolution.db`, `audit.db`)
- `langfuse-pgdata` — Langfuse Postgres
- `redis-data` — Redis AOF

Tear down (keeping data): `docker compose down`
Tear down (nuking data): `docker compose down -v`
