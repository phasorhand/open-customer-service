from datetime import UTC, datetime

import pytest

from opencs.channel.exec_token import InvalidTokenError, StubExecutionToken
from opencs.harness.action_plan import ActionPlan, RiskTier
from opencs.tools.executor import ToolExecutor
from opencs.tools.protocol import ToolDescription, ToolResult
from opencs.tools.registry import ToolRegistry


class _FakeTool:
    def __init__(self, result: ToolResult) -> None:
        self.tool_id = result.tool_id
        self._result = result
        self.call_count = 0

    def describe(self) -> ToolDescription:
        return ToolDescription(
            tool_id=self.tool_id,
            name=self.tool_id,
            description="test",
            parameters={},
            read_only=True,
        )

    async def call(self, args, token) -> ToolResult:
        self.call_count += 1
        return self._result

    async def dry_run(self, args) -> ToolResult:
        return self._result

    async def health_check(self) -> bool:
        return True


def _plan(tool_id: str = "crm.get_order", action_id: str = "act-1") -> ActionPlan:
    return ActionPlan(
        action_id=action_id,
        tool_id=tool_id,
        args={"order_id": "ord-001"},
        intent="look up order",
        risk_hint=RiskTier.GREEN,
    )


def _token(action_id: str = "act-1") -> StubExecutionToken:
    return StubExecutionToken(
        action_id=action_id,
        expires_at=datetime(2030, 1, 1, tzinfo=UTC),
    )


async def test_execute_calls_tool_and_returns_result() -> None:
    fake_result = ToolResult(tool_id="crm.get_order", success=True, data={"status": "shipped"})
    fake_tool = _FakeTool(fake_result)
    registry = ToolRegistry()
    registry.register(fake_tool)
    executor = ToolExecutor(registry=registry)

    result = await executor.execute(_plan(), _token())

    assert result.success is True
    assert result.data["status"] == "shipped"
    assert fake_tool.call_count == 1


async def test_execute_raises_on_token_action_id_mismatch() -> None:
    fake_result = ToolResult(tool_id="crm.get_order", success=True, data={})
    registry = ToolRegistry()
    registry.register(_FakeTool(fake_result))
    executor = ToolExecutor(registry=registry)

    wrong_token = _token(action_id="different-action")
    with pytest.raises(InvalidTokenError):
        await executor.execute(_plan(action_id="act-1"), wrong_token)


async def test_execute_raises_key_error_for_unknown_tool() -> None:
    registry = ToolRegistry()
    executor = ToolExecutor(registry=registry)

    with pytest.raises(KeyError):
        await executor.execute(_plan(tool_id="unknown.tool"), _token())
