# Milestones

## v1.0 — MVP (完成 2026-05-04)

**Goal:** Shippable minimum auditable customer service agent loop with HITL evolution and one-command Docker deployment.

**Phases:** 1–7c (7 phases, 10 plan documents)

| Phase | Name | Status |
|-------|------|--------|
| 1 | Channel Gateway | ✓ Complete |
| 2 | Harness + Agent Core | ✓ Complete |
| 3 | Memory + Skills | ✓ Complete |
| 4 | ToolProvider + CRM | ✓ Complete |
| 5 | Replay Engine | ✓ Complete |
| 6 | Evolution Layer | ✓ Complete |
| 7a | Backend Admin API | ✓ Complete |
| 7b | Admin Web UI | ✓ Complete |
| 7c | Docker Compose | ✓ Complete |

**Shipped:**
- 企微客服 + WebChat channel adapters
- Orchestrator + CS Reply + Approval Router workers
- ActionGuard (tiered risk) + AuditLog + HITL queue
- Skills Repo (bundled) + Memory (L0/L1/L2) + FTS5 search
- APIToolProvider + read-only CRM tool
- Replay engine (What-if / Strict / Partial) + verdict
- Evolution layer (Skill/Memory/CRM-Tool) + Shadow Runner + HITL
- Admin REST API + Next.js 14 Admin Web UI
- Docker Compose 5-service stack (api, web-ui, langfuse, postgres, redis)

**Deferred to v1.1:** OCR, CRM Explorer Agent, UIToolProvider, MCPToolProvider, auto-discovery, learned skills, 5-dim Evolution, vector search, batch replay, Feishu, K8s Helm chart
