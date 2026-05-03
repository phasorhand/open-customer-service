from opencs.tools.protocol import Tool, ToolDescription, ToolResult


def test_tool_description_construction() -> None:
    desc = ToolDescription(
        tool_id="crm.get_customer",
        name="Get Customer",
        description="Fetch customer by ID",
        parameters={"customer_id": {"type": "string"}},
        read_only=True,
    )
    assert desc.tool_id == "crm.get_customer"
    assert desc.read_only is True


def test_tool_result_success() -> None:
    result = ToolResult(tool_id="crm.get_customer", success=True, data={"id": "u1"})
    assert result.error is None
    assert result.data["id"] == "u1"


def test_tool_result_failure() -> None:
    result = ToolResult(
        tool_id="crm.get_customer", success=False, data={}, error="HTTP 404: Not found"
    )
    assert result.success is False
    assert result.error is not None


def test_tool_protocol_is_structural() -> None:
    """Tool is a structural Protocol — any object with the right methods satisfies it."""
    from opencs.channel.exec_token import ExecutionToken

    class FakeTool:
        tool_id = "fake.tool"

        def describe(self) -> ToolDescription:
            return ToolDescription(
                tool_id="fake.tool",
                name="Fake",
                description="Test tool",
                parameters={},
                read_only=True,
            )

        async def call(self, args: dict, token: ExecutionToken) -> ToolResult:
            return ToolResult(tool_id="fake.tool", success=True, data={})

        async def dry_run(self, args: dict) -> ToolResult:
            return ToolResult(tool_id="fake.tool", success=True, data={"_dry_run": True})

        async def health_check(self) -> bool:
            return True

    assert isinstance(FakeTool(), Tool)
