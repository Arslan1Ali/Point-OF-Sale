from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import app
from app.domain.auth.entities import UserRole
from tests.integration.api.helpers import login_as


async def _register_and_login(
    async_session,
    client: AsyncClient,
    *,
    role: UserRole = UserRole.INVENTORY,
    label: str | None = None,
) -> str:
    prefix = label or f"user_{uuid4().hex[:6]}"
    return await login_as(async_session, client, role, email_prefix=prefix)


async def _create_product(client: AsyncClient, token: str, *, name: str = "Prod1", sku: str | None = None) -> dict:
    unique_sku = sku or f"SKU{uuid4().hex[:8]}"
    resp = await client.post(
        "/api/v1/products",
        json={
            "name": name,
            "sku": unique_sku,
            "retail_price": "10.00",
            "purchase_price": "5.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _register_supplier(
    client: AsyncClient,
    token: str,
    *,
    name: str = "Supplier One",
    email: str | None = None,
    phone: str | None = None,
) -> dict:
    payload: dict[str, str] = {"name": name}
    if email is not None:
        payload["contact_email"] = email
    if phone is not None:
        payload["contact_phone"] = phone
    resp = await client.post(
        "/api/v1/suppliers",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _record_purchase_request(
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


async def _login_purchasing_and_manager(async_session, client: AsyncClient) -> tuple[str, str]:
    purchasing_token = await _register_and_login(async_session, client, role=UserRole.INVENTORY)
    manager_token = await _register_and_login(async_session, client, role=UserRole.MANAGER)
    return purchasing_token, manager_token


@pytest.mark.asyncio
async def test_record_purchase_restocks_inventory_and_returns_summary(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        purchasing_token, manager_token = await _login_purchasing_and_manager(async_session, client)
        product = await _create_product(client, manager_token)
        supplier = await _register_supplier(
            client,
            manager_token,
            name="Best Supplies",
            email=f"supplier_{uuid4().hex[:6]}@example.com",
        )

        body = await _record_purchase_request(
            client,
            purchasing_token,
            supplier_id=supplier["id"],
            product_id=product["id"],
            quantity=5,
            unit_cost="6.50",
        )
        purchase = body["purchase"]
        assert purchase["supplier_id"] == supplier["id"]
        assert purchase["total_quantity"] == 5
        assert purchase["total_amount"] == str(Decimal("6.50") * 5)
        assert len(purchase["items"]) == 1
        assert purchase["items"][0]["unit_cost"] == "6.50"
        assert body["movements"][0]["direction"] == "in"

        stock_resp = await client.get(
            f"/api/v1/products/{product['id']}/stock",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert stock_resp.status_code == 200, stock_resp.text
        stock = stock_resp.json()
        assert stock["quantity_on_hand"] == 5


@pytest.mark.asyncio
async def test_record_purchase_unknown_supplier_returns_404(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        purchasing_token, manager_token = await _login_purchasing_and_manager(async_session, client)
        product = await _create_product(client, manager_token)

        resp = await client.post(
            "/api/v1/purchases",
            json={
                "supplier_id": f"01{uuid4().hex[:24]}",
                "lines": [
                    {
                        "product_id": product["id"],
                        "quantity": 2,
                        "unit_cost": "6.00",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {purchasing_token}"},
        )
        assert resp.status_code == 404, resp.text
        payload = resp.json()
        assert payload["code"] == "not_found"


@pytest.mark.asyncio
async def test_record_purchase_unknown_product_returns_404(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        purchasing_token, manager_token = await _login_purchasing_and_manager(async_session, client)
        supplier = await _register_supplier(client, manager_token, name="Widgets Inc")

        resp = await client.post(
            "/api/v1/purchases",
            json={
                "supplier_id": supplier["id"],
                "lines": [
                    {
                        "product_id": f"01{uuid4().hex[:24]}",
                        "quantity": 1,
                        "unit_cost": "4.25",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {purchasing_token}"},
        )
        assert resp.status_code == 404, resp.text
        payload = resp.json()
        assert payload["code"] == "not_found"


@pytest.mark.asyncio
async def test_record_purchase_requires_positive_quantity(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        purchasing_token, manager_token = await _login_purchasing_and_manager(async_session, client)
        product = await _create_product(client, manager_token)
        supplier = await _register_supplier(client, manager_token, name="Quality Parts")

        resp = await client.post(
            "/api/v1/purchases",
            json={
                "supplier_id": supplier["id"],
                "lines": [
                    {
                        "product_id": product["id"],
                        "quantity": 0,
                        "unit_cost": "6.00",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {purchasing_token}"},
        )
        assert resp.status_code == 422, resp.text
        payload = resp.json()
        assert payload["detail"][0]["type"] == "greater_than"


@pytest.mark.asyncio
async def test_list_purchases_supports_supplier_filter(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        purchasing_token, manager_token = await _login_purchasing_and_manager(async_session, client)
        product = await _create_product(client, manager_token)
        supplier_a = await _register_supplier(client, manager_token, name="Alpha Supplies")
        supplier_b = await _register_supplier(client, manager_token, name="Beta Supplies")

        baseline_resp = await client.get(
            "/api/v1/purchases",
            headers={"Authorization": f"Bearer {purchasing_token}"},
        )
        assert baseline_resp.status_code == 200, baseline_resp.text
        baseline_total = baseline_resp.json()["meta"]["total"]

        order_a = await _record_purchase_request(
            client,
            purchasing_token,
            supplier_id=supplier_a["id"],
            product_id=product["id"],
            quantity=3,
            unit_cost="4.00",
        )
        order_b = await _record_purchase_request(
            client,
            purchasing_token,
            supplier_id=supplier_b["id"],
            product_id=product["id"],
            quantity=2,
            unit_cost="5.00",
        )

        list_resp = await client.get(
            "/api/v1/purchases",
            headers={"Authorization": f"Bearer {purchasing_token}"},
        )
        assert list_resp.status_code == 200, list_resp.text
        body = list_resp.json()
        assert body["meta"]["total"] == baseline_total + 2
        ids = {item["id"] for item in body["items"]}
        assert order_a["purchase"]["id"] in ids
        assert order_b["purchase"]["id"] in ids

        filter_resp = await client.get(
            "/api/v1/purchases",
            params={"supplier_id": supplier_a["id"]},
            headers={"Authorization": f"Bearer {purchasing_token}"},
        )
        assert filter_resp.status_code == 200, filter_resp.text
        filtered = filter_resp.json()
        assert filtered["meta"]["total"] == 1
        assert filtered["items"][0]["id"] == order_a["purchase"]["id"]


@pytest.mark.asyncio
async def test_get_purchase_returns_full_detail(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        purchasing_token, manager_token = await _login_purchasing_and_manager(async_session, client)
        product = await _create_product(client, manager_token)
        supplier = await _register_supplier(client, manager_token, name="Gamma Traders")

        order = await _record_purchase_request(
            client,
            purchasing_token,
            supplier_id=supplier["id"],
            product_id=product["id"],
            quantity=4,
            unit_cost="7.25",
        )
        purchase_id = order["purchase"]["id"]

        resp = await client.get(
            f"/api/v1/purchases/{purchase_id}",
            headers={"Authorization": f"Bearer {purchasing_token}"},
        )
        assert resp.status_code == 200, resp.text
        detail = resp.json()
        assert detail["id"] == purchase_id
        assert detail["supplier_id"] == supplier["id"]
        assert detail["total_amount"] == str(Decimal("7.25") * 4)
        assert detail["items"][0]["quantity"] == 4
