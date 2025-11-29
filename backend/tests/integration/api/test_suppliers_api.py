from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

from app.api.main import app
from app.domain.auth.entities import UserRole
from app.infrastructure.db.models.purchase_model import PurchaseOrderModel
from tests.integration.api.helpers import login_as


async def _login_user(
    async_session,
    client: AsyncClient,
    *,
    role: UserRole,
    label: str | None = None,
) -> str:
    prefix = label or f"user_{uuid4().hex[:6]}"
    return await login_as(async_session, client, role, email_prefix=prefix)


async def _create_supplier(
    client: AsyncClient,
    token: str,
    *,
    name: str = "Acme Supplies",
) -> dict:
    resp = await client.post(
        "/api/v1/suppliers",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_product(
    client: AsyncClient,
    token: str,
    *,
    name: str = "Widget",
    sku: str | None = None,
    purchase_price: str = "5.00",
    retail_price: str = "10.00",
) -> dict:
    resp = await client.post(
        "/api/v1/products",
        json={
            "name": name,
            "sku": sku or f"SKU{uuid4().hex[:8]}",
            "purchase_price": purchase_price,
            "retail_price": retail_price,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _record_purchase(
    client: AsyncClient,
    token: str,
    *,
    supplier_id: str,
    product_id: str,
    quantity: int,
    unit_cost: str,
) -> dict:
    resp = await client.post(
        "/api/v1/purchases",
        json={
            "supplier_id": supplier_id,
            "lines": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_cost": unit_cost,
                }
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_get_supplier_summary_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/suppliers/01HZZUNKNOWN/summary")
        assert resp.status_code == 401
        payload = resp.json()
        assert payload["code"] == "unauthorized"
        assert payload["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_get_supplier_summary_returns_aggregates(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        manager_token = await _login_user(async_session, client, role=UserRole.MANAGER)
        purchasing_token = await _login_user(async_session, client, role=UserRole.INVENTORY)

        supplier = await _create_supplier(client, manager_token, name="Prime Supplies")
        product = await _create_product(client, manager_token)

        first_order = await _record_purchase(
            client,
            purchasing_token,
            supplier_id=supplier["id"],
            product_id=product["id"],
            quantity=3,
            unit_cost="6.50",
        )
        second_order = await _record_purchase(
            client,
            purchasing_token,
            supplier_id=supplier["id"],
            product_id=product["id"],
            quantity=2,
            unit_cost="7.25",
        )

        first_created = datetime.fromisoformat(first_order["purchase"]["created_at"])
        second_created = datetime.fromisoformat(second_order["purchase"]["created_at"])

        await async_session.execute(
            update(PurchaseOrderModel)
            .where(PurchaseOrderModel.id == first_order["purchase"]["id"])
            .values(received_at=first_created + timedelta(hours=4, minutes=30))
        )
        await async_session.execute(
            update(PurchaseOrderModel)
            .where(PurchaseOrderModel.id == second_order["purchase"]["id"])
            .values(received_at=second_created + timedelta(hours=9, minutes=30))
        )
        await async_session.commit()

        summary_resp = await client.get(
            f"/api/v1/suppliers/{supplier['id']}/summary",
            headers={"Authorization": f"Bearer {purchasing_token}"},
        )
        assert summary_resp.status_code == 200, summary_resp.text
        summary = summary_resp.json()

        total_amount = Decimal("6.50") * 3 + Decimal("7.25") * 2

        assert summary["supplier_id"] == supplier["id"]
        assert summary["currency"] == "USD"
        assert summary["total_orders"] == 2
        assert summary["total_quantity"] == 5
        assert summary["total_amount"] == format(total_amount, "0.2f")
        assert summary["average_order_value"] == format(total_amount / Decimal(2), "0.2f")
        assert summary["average_lead_time_hours"] == "7.00"
        assert summary["first_order_at"] is not None
        assert summary["last_order_at"] is not None
        assert summary["last_order_id"] == second_order["purchase"]["id"]
        assert summary["last_order_amount"] == format(Decimal(second_order["purchase"]["total_amount"]), "0.2f")
        assert summary["open_orders"] == 0


@pytest.mark.asyncio
async def test_get_supplier_summary_handles_no_orders(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        manager_token = await _login_user(async_session, client, role=UserRole.MANAGER)
        viewer_token = await _login_user(async_session, client, role=UserRole.AUDITOR)

        supplier = await _create_supplier(client, manager_token, name="Empty Supplier")

        summary_resp = await client.get(
            f"/api/v1/suppliers/{supplier['id']}/summary",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert summary_resp.status_code == 200, summary_resp.text
        summary = summary_resp.json()

        assert summary["supplier_id"] == supplier["id"]
        assert summary["total_orders"] == 0
        assert summary["total_quantity"] == 0
        assert summary["total_amount"] == "0.00"
        assert summary["average_order_value"] is None
        assert summary["average_lead_time_hours"] is None
        assert summary["currency"] is None
        assert summary["first_order_at"] is None
        assert summary["last_order_at"] is None
        assert summary["last_order_id"] is None
        assert summary["last_order_amount"] is None
        assert summary["open_orders"] == 0
