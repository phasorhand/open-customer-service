# Phase 4 — ToolProvider + CRM Read-Only Tools

## Goal

Build the `ToolProvider` abstraction (§3.7) so Workers can produce `ActionPlan`s targeting arbitrary tools (not just `channel.send`), and the Orchestrator can execute approved plans via a `ToolExecutor`. Deliver a sample read-only CRM tool backed by a mock service to prove the E2E flow.

## Scope (MVP)

**In scope:**
- `Tool` protocol: `describe()` / `call(args, token)` / `dry_run(args)` / `health_check()`
- `ToolRegistry`: holds tools by `tool_id`, lookup + list
- `APITool`: HTTP-based tool that executes a configured endpoint (method, URL template, params)
- `ToolExecutor`: validates `ExecutionToken`, resolves tool from registry, calls it
- Mock CRM service: in-memory stub exposing `GET /customers/{id}` and `GET /orders/{id}`
- Two registered tools: `crm.get_customer` (Green) and `crm.get_order` (Green)
- Orchestrator `_execute_plan` extended to dispatch non-`channel.send` plans to `ToolExecutor`
- `CSReplyWorker` extended to produce CRM lookup plans when customer asks about their order

**Out of scope (v1):**
- `UIToolProvider`, `MCPToolProvider`
- Write tools (Yellow/Orange/Red tier CRM mutations)
- OpenAPI auto-discovery / schema import
- Tool lifecycle management by Evolution layer
- CRM Explorer Agent

## Architecture

```
Worker → ActionPlan(tool_id="crm.get_order", args={...}, risk_hint=GREEN)
    ↓
Orchestrator → ActionGuard.evaluate(plan)
    ↓ (auto_approved + token)
ToolExecutor.execute(plan, token)
    ↓
ToolRegistry.get("crm.get_order") → APITool
    ↓
APITool.call(args, token) → verifies token → HTTP GET → returns result dict
    ↓
Orchestrator receives result → (future: feeds back to worker for multi-step)
```

## Components

### Tool Protocol

```python
class Tool(Protocol):
    tool_id: str

    def describe(self) -> ToolDescription:
        """Return schema: name, description, parameters, return type."""
        ...

    async def call(self, args: dict[str, object], token: ExecutionToken) -> ToolResult:
        """Execute the tool. Token must be valid for this tool_id + args."""
        ...

    async def dry_run(self, args: dict[str, object]) -> ToolResult:
        """Read-only preview. No token required. Returns example/schema."""
        ...

    async def health_check(self) -> bool:
        """Returns True if the tool's backing service is reachable."""
        ...
```

### ToolDescription

```python
@dataclass
class ToolDescription:
    tool_id: str
    name: str
    description: str
    parameters: dict[str, object]  # JSON Schema for args
    read_only: bool
```

### ToolResult

```python
@dataclass
class ToolResult:
    tool_id: str
    success: bool
    data: dict[str, object]  # structured response
    error: str | None = None
```

### ToolRegistry

```python
class ToolRegistry:
    def register(self, tool: Tool) -> None: ...
    def get(self, tool_id: str) -> Tool: ...  # raises KeyError if missing
    def list_tools(self) -> list[ToolDescription]: ...
```

### APITool

Configured with:
- `tool_id`: e.g. `"crm.get_customer"`
- `base_url`: e.g. `"http://localhost:8001"`
- `method`: `"GET"` | `"POST"`
- `path_template`: e.g. `"/customers/{customer_id}"`
- `parameters_schema`: JSON Schema dict for args validation
- `read_only`: bool (MVP: always True)

`call()` interpolates args into the path template, makes the HTTP request (via `httpx`), returns structured `ToolResult`.

### ToolExecutor

```python
class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None: ...

    async def execute(self, plan: ActionPlan, token: ExecutionToken) -> ToolResult:
        """Verify token, resolve tool, call it."""
        token.verify(action_id=plan.action_id)
        tool = self._registry.get(plan.tool_id)
        return await tool.call(plan.args, token)
```

### Mock CRM

An in-memory dict-backed service. For tests, exposed as fixture data. For the dev server, optionally mounted as FastAPI sub-routes at `/mock-crm/`.

Data:
```python
CUSTOMERS = {
    "u1": {"id": "u1", "name": "Alice", "tier": "VIP", "email": "alice@example.com"},
    "u2": {"id": "u2", "name": "Bob", "tier": "standard", "email": "bob@example.com"},
}
ORDERS = {
    "ord-001": {"id": "ord-001", "customer_id": "u1", "status": "shipped", "total": 199.0},
    "ord-002": {"id": "ord-002", "customer_id": "u2", "status": "pending", "total": 49.5},
}
```

### Orchestrator Changes

`_execute_plan` currently only handles `channel.send`. Extended:

```python
async def _execute_plan(self, plan, *, token):
    if plan.tool_id == "channel.send":
        # existing webchat send logic
        ...
    elif self._tool_executor:
        result = await self._tool_executor.execute(plan, token)
        # MVP: log result to L0; future: feed back to worker for multi-step
        ...
```

## File Structure

```
src/opencs/
  tools/
    RESEARCH.md
    __init__.py
    protocol.py         # Tool protocol, ToolDescription, ToolResult
    registry.py         # ToolRegistry
    api_tool.py         # APITool implementation
    executor.py         # ToolExecutor
    mock_crm.py         # Mock CRM data + optional FastAPI routes

tests/
  tools/
    __init__.py
    test_api_tool.py
    test_registry.py
    test_executor.py
    test_mock_crm.py
  test_e2e_tool_execution.py
```

## Dependencies

- `httpx` — async HTTP client for `APITool.call()` (MIT, actively maintained, already common in FastAPI projects)
- No other new dependencies

## Risk Tier Mapping

| Tool | Tier | Rationale |
|---|---|---|
| `crm.get_customer` | Green | Read-only, no side effects |
| `crm.get_order` | Green | Read-only, no side effects |
| (future write tools) | Yellow/Orange/Red | Deferred to v1 |

## Integration with Phase 3

- `ToolExecutor` results can be written to L0 as `"tool_result"` events
- `MemoryStore.load_context()` unchanged — tool results flow through `session_context` in multi-turn scenarios
- Workers produce `ActionPlan` with `tool_id="crm.get_order"` alongside `tool_id="channel.send"` — both go through ActionGuard

## Hand-off Contract for Phase 5 (Replay)

- `L0RawEventStore` gains `kind="tool_call"` and `kind="tool_result"` events
- `ToolExecutor` writes both pre-call and post-call events to L0
- Replay can reconstruct tool call traces from L0 without re-executing
