from __future__ import annotations

from typing import TYPE_CHECKING

from opencs.replay.types import ReplayMode
from opencs.tools.protocol import ToolResult

if TYPE_CHECKING:
    from opencs.channel.exec_token import ExecutionToken
    from opencs.harness.action_plan import ActionPlan
    from opencs.tools.executor import ToolExecutor


class ReplayingToolExecutor:
    """Tool executor wrapper for replay: serves cached results or delegates.

    - STRICT: always serve from cache (by action_id); fall back to real if cache miss.
    - PARTIAL: same as STRICT — tools always cached.
    - WHAT_IF: serve from cache UNLESS tool_id is in tool_ids_to_rerun.
    """

    def __init__(
        self,
        *,
        mode: ReplayMode,
        tool_cache: dict[str, dict[str, object]],
        real_executor: ToolExecutor,
        tool_ids_to_rerun: list[str],
    ) -> None:
        self._mode = mode
        self._cache = tool_cache
        self._real = real_executor
        self._rerun_ids = set(tool_ids_to_rerun)

    async def execute(self, plan: ActionPlan, token: ExecutionToken) -> ToolResult:
        if self._mode == ReplayMode.WHAT_IF and plan.tool_id in self._rerun_ids:
            return await self._real.execute(plan, token)

        cached = self._cache.get(plan.action_id)
        if cached is not None:
            return ToolResult(
                tool_id=plan.tool_id,
                success=bool(cached.get("success")),
                data=dict(cached.get("data") or {}),
                error=cached.get("error") if cached.get("error") else None,
            )

        return await self._real.execute(plan, token)
