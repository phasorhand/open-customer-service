from datetime import UTC, datetime

import pytest

from opencs.channel.exec_token import StubExecutionToken
from opencs.harness.action_plan import ActionPlan, RiskTier
from opencs.replay.replaying_tool import ReplayingToolExecutor
from opencs.replay.types import ReplayMode
from opencs.tools.executor import ToolExecutor
from opencs.tools.protocol import ToolDescription, ToolResult
from opencs.tools.registry import ToolRegistry


def _token(action_id: str = "act-1") -> StubExecutionToken:
    return StubExecutionToken(action_id=action_id, expires_at=datetime(2030, 1, 1, tzinfo=UTC))


def _plan(action_id: str = "act-1", tool_id: str = "crm.get_order") -> ActionPlan:
    return ActionPlan(
        action_id=action_id,
        tool_id=tool_id,
        args={"order_id": "ord-001"},
        intent="lookup",
        risk_hint=RiskTier.GREEN,
    )


class _FakeTool:
    def __init__(self, tool_id: str, data: dict) -> None:
        self.tool_id = tool_id
        self._data = data
        self.call_count = 0

    def describe(self) -> ToolDescription:
        return ToolDescription(tool_id=self.tool_id, name=self.tool_id, description="", parameters={}, read_only=True)

    async def call(self, args, token) -> ToolResult:
        self.call_count += 1
        return ToolResult(tool_id=self.tool_id, success=True, data=self._data)

    async def dry_run(self, args) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={"_dry_run": True})

    async def health_check(self) -> bool:
        return True


async def test_strict_mode_serves_from_cache() -> None:
    cache = {"act-1": {"success": True, "data": {"status": "shipped"}, "error": None}}
    reg = ToolRegistry()
    fake_tool = _FakeTool("crm.get_order", {"status": "new_data"})
    reg.register(fake_tool)
    real_executor = ToolExecutor(registry=reg)

    replaying = ReplayingToolExecutor(
        mode=ReplayMode.STRICT,
        tool_cache=cache,
        real_executor=real_executor,
        tool_ids_to_rerun=[],
    )
    result = await replaying.execute(_plan(), _token())
    assert result.success is True
    assert result.data["status"] == "shipped"
    assert fake_tool.call_count == 0


async def test_what_if_with_override_reruns_tool() -> None:
    cache = {"act-1": {"success": True, "data": {"status": "old"}, "error": None}}
    reg = ToolRegistry()
    fake_tool = _FakeTool("crm.get_order", {"status": "new_from_real"})
    reg.register(fake_tool)
    real_executor = ToolExecutor(registry=reg)

    replaying = ReplayingToolExecutor(
        mode=ReplayMode.WHAT_IF,
        tool_cache=cache,
        real_executor=real_executor,
        tool_ids_to_rerun=["crm.get_order"],
    )
    result = await replaying.execute(_plan(), _token())
    assert result.data["status"] == "new_from_real"
    assert fake_tool.call_count == 1


async def test_what_if_without_override_serves_cache() -> None:
    cache = {"act-1": {"success": True, "data": {"status": "cached"}, "error": None}}
    reg = ToolRegistry()
    fake_tool = _FakeTool("crm.get_order", {"status": "real"})
    reg.register(fake_tool)
    real_executor = ToolExecutor(registry=reg)

    replaying = ReplayingToolExecutor(
        mode=ReplayMode.WHAT_IF,
        tool_cache=cache,
        real_executor=real_executor,
        tool_ids_to_rerun=[],  # no tool overrides
    )
    result = await replaying.execute(_plan(), _token())
    assert result.data["status"] == "cached"
    assert fake_tool.call_count == 0


async def test_partial_mode_serves_cache() -> None:
    cache = {"act-1": {"success": True, "data": {"status": "cached"}, "error": None}}
    reg = ToolRegistry()
    fake_tool = _FakeTool("crm.get_order", {"status": "real"})
    reg.register(fake_tool)
    real_executor = ToolExecutor(registry=reg)

    replaying = ReplayingToolExecutor(
        mode=ReplayMode.PARTIAL,
        tool_cache=cache,
        real_executor=real_executor,
        tool_ids_to_rerun=[],
    )
    result = await replaying.execute(_plan(), _token())
    assert result.data["status"] == "cached"
    assert fake_tool.call_count == 0


async def test_cache_miss_falls_through_to_real() -> None:
    cache: dict = {}  # no cache entry for this action_id
    reg = ToolRegistry()
    fake_tool = _FakeTool("crm.get_order", {"status": "from_real"})
    reg.register(fake_tool)
    real_executor = ToolExecutor(registry=reg)

    replaying = ReplayingToolExecutor(
        mode=ReplayMode.STRICT,
        tool_cache=cache,
        real_executor=real_executor,
        tool_ids_to_rerun=[],
    )
    result = await replaying.execute(_plan(), _token())
    assert result.data["status"] == "from_real"
    assert fake_tool.call_count == 1
