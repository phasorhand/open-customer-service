from __future__ import annotations

from opencs.tools.protocol import Tool, ToolDescription


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.tool_id] = tool

    def get(self, tool_id: str) -> Tool:
        try:
            return self._tools[tool_id]
        except KeyError as err:
            raise KeyError(tool_id) from err

    def list_tools(self) -> list[ToolDescription]:
        return [tool.describe() for tool in self._tools.values()]
