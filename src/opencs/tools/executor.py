from __future__ import annotations

from typing import TYPE_CHECKING

from opencs.tools.protocol import ToolResult  # needed for mypy return annotation
from opencs.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from opencs.channel.exec_token import ExecutionToken
    from opencs.harness.action_plan import ActionPlan


class ToolExecutor:
    """Verifies ExecutionToken, resolves tool from registry, and calls it."""

    def __init__(self, *, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(self, plan: ActionPlan, token: ExecutionToken) -> ToolResult:
        token.verify(action_id=plan.action_id)
        tool = self._registry.get(plan.tool_id)
        return await tool.call(plan.args, token)
