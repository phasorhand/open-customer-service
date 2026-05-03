from datetime import UTC, datetime

import httpx
import pytest
from fastapi import FastAPI

from opencs.channel.exec_token import StubExecutionToken
from opencs.tools.api_tool import APITool
from opencs.tools.mock_crm import router as crm_router


def _stub_token(action_id: str = "act-1") -> StubExecutionToken:
    return StubExecutionToken(
        action_id=action_id,
        expires_at=datetime(2030, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def crm_transport() -> httpx.ASGITransport:
    app = FastAPI()
    app.include_router(crm_router)
    return httpx.ASGITransport(app=app)


@pytest.fixture
def customer_tool(crm_transport: httpx.ASGITransport) -> APITool:
    return APITool(
        tool_id="crm.get_customer",
        base_url="http://test",
        method="GET",
        path_template="/mock-crm/customers/{customer_id}",
        parameters_schema={"customer_id": {"type": "string"}},
        read_only=True,
        _transport=crm_transport,
    )


@pytest.fixture
def order_tool(crm_transport: httpx.ASGITransport) -> APITool:
    return APITool(
        tool_id="crm.get_order",
        base_url="http://test",
        method="GET",
        path_template="/mock-crm/orders/{order_id}",
        parameters_schema={"order_id": {"type": "string"}},
        read_only=True,
        _transport=crm_transport,
    )


async def test_call_get_customer_success(customer_tool: APITool) -> None:
    result = await customer_tool.call({"customer_id": "u1"}, _stub_token())
    assert result.success is True
    assert result.data["name"] == "Alice"
    assert result.tool_id == "crm.get_customer"


async def test_call_get_customer_not_found(customer_tool: APITool) -> None:
    result = await customer_tool.call({"customer_id": "unknown"}, _stub_token())
    assert result.success is False
    assert result.error is not None
    assert "404" in result.error


async def test_call_get_order_success(order_tool: APITool) -> None:
    result = await order_tool.call({"order_id": "ord-001"}, _stub_token())
    assert result.success is True
    assert result.data["status"] == "shipped"


async def test_dry_run_returns_dry_run_flag(customer_tool: APITool) -> None:
    result = await customer_tool.dry_run({"customer_id": "u1"})
    assert result.success is True
    assert result.data.get("_dry_run") is True


def test_describe_returns_tool_description(customer_tool: APITool) -> None:
    desc = customer_tool.describe()
    assert desc.tool_id == "crm.get_customer"
    assert desc.read_only is True
