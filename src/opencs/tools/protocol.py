from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from opencs.channel.exec_token import ExecutionToken


@dataclass
class ToolDescription:
    tool_id: str
    name: str
    description: str
    parameters: dict[str, object]
    read_only: bool


@dataclass
class ToolResult:
    tool_id: str
    success: bool
    data: dict[str, object]
    error: str | None = field(default=None)


@runtime_checkable
class Tool(Protocol):
    tool_id: str

    def describe(self) -> ToolDescription: ...

    async def call(self, args: dict[str, object], token: ExecutionToken) -> ToolResult: ...

    async def dry_run(self, args: dict[str, object]) -> ToolResult: ...

    async def health_check(self) -> bool: ...
