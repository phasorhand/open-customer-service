# Phase 4 ToolProvider + CRM Read-Only Tools — close note

## Delivered
- `Tool` Protocol — structural interface: `describe() / call(args, token) / dry_run(args) / health_check()`
- `ToolDescription` + `ToolResult` dataclasses
- `ToolRegistry` — register / get / list_tools; KeyError on unknown tool_id
- `APITool` — httpx-based HTTP tool with path-template interpolation; `_transport` injection for in-process testing
- `ToolExecutor` — verifies `ExecutionToken` before resolving tool and calling it; security boundary preserved
- Mock CRM service — in-memory `CUSTOMERS` + `ORDERS` dicts; FastAPI router at `/mock-crm/`; two registered tools: `crm.get_customer` (Green) and `crm.get_order` (Green)
- `Orchestrator` extended — optional `tool_executor` param; `_execute_plan` routes non-`channel.send` plans to `ToolExecutor`; writes `tool_call` and `tool_result` L0 events before/after execution
- `CSReplyWorker` extended — `_ORDER_RE` regex detects `ord-*` patterns; emits GREEN `crm.get_order` plan before `channel.send` plan
- `main.py` updated — wires `ToolRegistry` with both CRM tools; `ToolExecutor` injected into Orchestrator; mock CRM router mounted
- `ExecutionToken` Protocol — attributes changed to `@property` to correctly accept frozen dataclass implementations

## Tests
`uv run pytest -v` — 138 tests passing (up from 108 in Phase 3).

## Known deferrals (intentional)
- `UIToolProvider`, `MCPToolProvider` → v1
- Write tools (Yellow/Orange/Red CRM mutations) → v1
- OpenAPI auto-discovery / schema import → v1
- CRM Explorer Agent → v1
- Multi-order detection in a single message (regex captures only first `ord-*`) → v1
- `channel_id` not propagated in `CSReplyWorker`'s `channel.send` args (defaults to `webchat`) — known gap before multi-channel expansion
- ToolExecutor result fed back to worker for multi-step reasoning → Phase 5/v1

## Hand-off contract for Phase 5 (Replay)
- `L0RawEventStore` now has `kind="tool_call"` and `kind="tool_result"` events; payloads include `action_id`, `tool_id`, `args`, `success`, `data`, `error`
- `ToolExecutor` writes pre-call and post-call events atomically via Orchestrator
- Replay can reconstruct full tool-call traces from L0 without re-executing any tools
- `ToolRegistry` is independent of Memory and Channel; Replay can construct its own read-only registry instance
- All tool calls are GREEN tier in MVP — auto-approved; no HITL trace records needed for CRM lookups
