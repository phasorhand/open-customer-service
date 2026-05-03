from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from opencs.tools.protocol import ToolDescription, ToolResult

if TYPE_CHECKING:
    from opencs.channel.exec_token import ExecutionToken


class APITool:
    """HTTP-based tool that executes a configured endpoint via httpx."""

    def __init__(
        self,
        *,
        tool_id: str,
        base_url: str,
        method: str,
        path_template: str,
        parameters_schema: dict[str, object],
        read_only: bool = True,
        _transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.tool_id = tool_id
        self._base_url = base_url
        self._method = method.upper()
        self._path_template = path_template
        self._parameters_schema = parameters_schema
        self._read_only = read_only
        self._transport = _transport

    def describe(self) -> ToolDescription:
        return ToolDescription(
            tool_id=self.tool_id,
            name=self.tool_id,
            description=f"HTTP {self._method} {self._path_template}",
            parameters=self._parameters_schema,
            read_only=self._read_only,
        )

    async def call(self, args: dict[str, object], token: ExecutionToken) -> ToolResult:
        path = self._path_template.format(**{k: str(v) for k, v in args.items()})
        async with httpx.AsyncClient(
            base_url=self._base_url, transport=self._transport
        ) as client:
            resp = await client.request(self._method, path)
        if resp.status_code >= 400:
            return ToolResult(
                tool_id=self.tool_id,
                success=False,
                data={},
                error=f"HTTP {resp.status_code}: {resp.text}",
            )
        return ToolResult(tool_id=self.tool_id, success=True, data=resp.json())

    async def dry_run(self, args: dict[str, object]) -> ToolResult:
        return ToolResult(
            tool_id=self.tool_id,
            success=True,
            data={"_dry_run": True, "args": dict(args)},
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, transport=self._transport
            ) as client:
                await client.get("/")
            return True
        except Exception:
            return False
