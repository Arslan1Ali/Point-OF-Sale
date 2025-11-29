from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import app
from app.domain.auth.entities import UserRole
from tests.integration.api.helpers import create_user_and_login


@pytest.mark.asyncio
async def test_create_product_unauthorized():
    unique_sku = f"SKU{uuid4().hex[:8]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/products", json={
            "name": "Prod1",
            "sku": unique_sku,
            "retail_price": "10.00",
            "purchase_price": "5.00"
        })
        assert resp.status_code == 401, resp.text
        payload = resp.json()
        assert payload["code"] == "unauthorized"
        assert payload["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_create_product_authorized(async_session):
    # Register & login to get token
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await create_user_and_login(async_session, client, unique_email, "Secretp@ss1", UserRole.MANAGER)

        unique_sku = f"SKU{uuid4().hex[:8]}"
        resp = await client.post(
            "/api/v1/products",
            json={
                "name": "Prod1",
                "sku": unique_sku,
                "retail_price": "10.00",
                "purchase_price": "5.00"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["sku"] == unique_sku
        assert resp.headers.get("X-Trace-Id")
        assert data["version"] == 0


async def _register_and_login(async_session, client: AsyncClient, email: str, password: str = "Secretp@ss1") -> str:
    return await create_user_and_login(async_session, client, email, password, UserRole.MANAGER)


async def _create_product(client: AsyncClient, token: str, *, sku: str | None = None) -> dict:
    unique_sku = sku or f"SKU{uuid4().hex[:8]}"
    resp = await client.post(
        "/api/v1/products",
        json={
            "name": "Prod1",
            "sku": unique_sku,
            "retail_price": "10.00",
            "purchase_price": "5.00"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_update_product_success(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        created = await _create_product(client, token)

        resp = await client.patch(
            f"/api/v1/products/{created['id']}",
            json={
                "expected_version": created["version"],
                "name": "Updated",
                "retail_price": "12.00",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        payload = resp.json()
        assert payload["name"] == "Updated"
        assert payload["retail_price"] == "12.00"
        assert payload["purchase_price"] == "5.00"
        assert payload["version"] == created["version"] + 2
        assert resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_update_product_conflict_on_version(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        created = await _create_product(client, token)

        resp = await client.patch(
            f"/api/v1/products/{created['id']}",
            json={
                "expected_version": created["version"] + 5,
                "name": "Updated"
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409
        payload = resp.json()
        assert payload["code"] == "conflict"
        assert payload["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_update_product_requires_changes(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        created = await _create_product(client, token)

        resp = await client.patch(
            f"/api/v1/products/{created['id']}",
            json={"expected_version": created["version"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        payload = resp.json()
        assert payload["code"] == "validation_error"
        assert payload["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_deactivate_product_success(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        created = await _create_product(client, token)

        resp = await client.post(
            f"/api/v1/products/{created['id']}/deactivate",
            json={"expected_version": created["version"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        payload = resp.json()
        assert payload["active"] is False
        assert payload["version"] == created["version"] + 1
        assert resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_deactivate_product_already_inactive(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        created = await _create_product(client, token)

        first = await client.post(
            f"/api/v1/products/{created['id']}/deactivate",
            json={"expected_version": created["version"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert first.status_code == 200, first.text
        second = await client.post(
            f"/api/v1/products/{created['id']}/deactivate",
            json={"expected_version": first.json()["version"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert second.status_code == 400
        payload = second.json()
        assert payload["code"] == "validation_error"
        assert payload["trace_id"] == second.headers.get("X-Trace-Id")
