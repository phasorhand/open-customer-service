"""In-memory mock CRM data and FastAPI router for development and testing."""

from fastapi import APIRouter, HTTPException

CUSTOMERS: dict[str, dict[str, object]] = {
    "u1": {"id": "u1", "name": "Alice", "tier": "VIP", "email": "alice@example.com"},
    "u2": {"id": "u2", "name": "Bob", "tier": "standard", "email": "bob@example.com"},
}

ORDERS: dict[str, dict[str, object]] = {
    "ord-001": {"id": "ord-001", "customer_id": "u1", "status": "shipped", "total": 199.0},
    "ord-002": {"id": "ord-002", "customer_id": "u2", "status": "pending", "total": 49.5},
}

router = APIRouter(prefix="/mock-crm")


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str) -> dict[str, object]:
    if customer_id not in CUSTOMERS:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CUSTOMERS[customer_id]


@router.get("/orders/{order_id}")
async def get_order(order_id: str) -> dict[str, object]:
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="Order not found")
    return ORDERS[order_id]
