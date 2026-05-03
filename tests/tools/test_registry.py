import pytest

from opencs.tools.protocol import ToolDescription, ToolResult
from opencs.tools.registry import ToolRegistry


class _FakeTool:
    def __init__(self, tool_id: str) -> None:
        self.tool_id = tool_id

    def describe(self) -> ToolDescription:
        return ToolDescription(
            tool_id=self.tool_id,
            name=self.tool_id,
            description="test",
            parameters={},
            read_only=True,
        )

    async def call(self, args, token) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={})

    async def dry_run(self, args) -> ToolResult:
        return ToolResult(tool_id=self.tool_id, success=True, data={"_dry_run": True})

    async def health_check(self) -> bool:
        return True


def test_register_and_get() -> None:
    reg = ToolRegistry()
    tool = _FakeTool("crm.get_customer")
    reg.register(tool)
    assert reg.get("crm.get_customer") is tool


def test_get_missing_raises_key_error() -> None:
    reg = ToolRegistry()
    with pytest.raises(KeyError, match="no_such_tool"):
        reg.get("no_such_tool")


def test_list_tools_returns_descriptions() -> None:
    reg = ToolRegistry()
    reg.register(_FakeTool("crm.get_customer"))
    reg.register(_FakeTool("crm.get_order"))
    descs = reg.list_tools()
    ids = {d.tool_id for d in descs}
    assert ids == {"crm.get_customer", "crm.get_order"}


def test_register_overwrites_existing_tool_id() -> None:
    reg = ToolRegistry()
    old = _FakeTool("crm.get_customer")
    new = _FakeTool("crm.get_customer")
    reg.register(old)
    reg.register(new)
    assert reg.get("crm.get_customer") is new
