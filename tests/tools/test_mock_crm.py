import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from opencs.tools.mock_crm import CUSTOMERS, ORDERS, router


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_customers_data_integrity() -> None:
    assert "u1" in CUSTOMERS
    assert CUSTOMERS["u1"]["name"] == "Alice"
    assert CUSTOMERS["u2"]["tier"] == "standard"


def test_orders_data_integrity() -> None:
    assert "ord-001" in ORDERS
    assert ORDERS["ord-001"]["customer_id"] == "u1"
    assert ORDERS["ord-002"]["status"] == "pending"


def test_get_customer_endpoint(client: TestClient) -> None:
    resp = client.get("/mock-crm/customers/u1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alice"


def test_get_customer_not_found(client: TestClient) -> None:
    resp = client.get("/mock-crm/customers/missing")
    assert resp.status_code == 404


def test_get_order_endpoint(client: TestClient) -> None:
    resp = client.get("/mock-crm/orders/ord-001")
    assert resp.status_code == 200
    assert resp.json()["status"] == "shipped"


def test_get_order_not_found(client: TestClient) -> None:
    resp = client.get("/mock-crm/orders/missing-order")
    assert resp.status_code == 404
