# OpenCS

Open-source, self-hosted private-domain customer-service AI platform.

See `docs/superpowers/specs/2026-04-30-open-cs-mvp-architecture.md` for the full architecture.

## Dev quickstart

```bash
uv sync --all-groups
uv run pytest
uv run uvicorn opencs.gateway.app:create_default_app --factory --reload
```
