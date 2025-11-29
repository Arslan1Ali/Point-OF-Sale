from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import app
from app.domain.auth.entities import UserRole
from tests.integration.api.helpers import create_user_and_login


async def _register_and_login(async_session, client: AsyncClient, email: str, password: str = "Secretp@ss1") -> str:
    return await create_user_and_login(async_session, client, email, password, UserRole.MANAGER)


@pytest.mark.asyncio
async def test_create_category_unauthorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/categories",
            json={"name": "Beverages"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["code"] == "unauthorized"
        assert data["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_create_category_authorized(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    category_name = f"Beverages-{uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        resp = await client.post(
            "/api/v1/categories",
            json={"name": category_name, "description": "Drinks"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, resp.text
        payload = resp.json()
        assert payload["name"] == category_name
        expected_slug = (
            category_name.lower().replace(" ", "-")
            if " " in category_name
            else category_name.lower()
        )
        assert payload["slug"] == expected_slug
        assert payload["description"] == "Drinks"
        assert payload["version"] == 0
        assert resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_create_category_conflict(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    base_name = f"Beverages-{uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        first = await client.post(
            "/api/v1/categories",
            json={"name": base_name},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert first.status_code == 201, first.text
        dup = await client.post(
            "/api/v1/categories",
            json={"name": base_name},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert dup.status_code == 409
        payload = dup.json()
        assert payload["code"] == "conflict"
        assert payload["trace_id"] == dup.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_list_categories_returns_created_entries(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    prefix = f"Browse-{uuid4().hex[:4]}"
    names_to_create = [f"{prefix}-Beverages", f"{prefix}-Snacks"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        for name in names_to_create:
            resp = await client.post(
                "/api/v1/categories",
                json={"name": name},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 201, resp.text

        listing = await client.get(
            "/api/v1/categories",
            params={"search": prefix},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert listing.status_code == 200, listing.text
        payload = listing.json()
        names = {item["name"] for item in payload["items"]}
        assert set(names_to_create).issubset(names)
        assert payload["meta"]["total"] == len(names_to_create)
        assert payload["meta"]["page"] == 1
        assert payload["meta"]["limit"] == 20


@pytest.mark.asyncio
async def test_list_categories_supports_pagination_and_search(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    prefix = f"PhaseTwo-{uuid4().hex[:4]}"
    names_to_create = [f"{prefix}-Drinks", f"{prefix}-Snacks", f"Misc-{uuid4().hex[:4]}"]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        for name in names_to_create:
            resp = await client.post(
                "/api/v1/categories",
                json={"name": name},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 201, resp.text

        first_page = await client.get(
            "/api/v1/categories",
            params={"limit": 1, "page": 1, "search": prefix},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert first_page.status_code == 200, first_page.text
        first_payload = first_page.json()
        assert first_payload["meta"]["total"] == 2
        assert first_payload["meta"]["pages"] == 2
        assert len(first_payload["items"]) == 1
        assert first_payload["items"][0]["name"].startswith(prefix)

        second_page = await client.get(
            "/api/v1/categories",
            params={"limit": 1, "page": 2, "search": prefix},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert second_page.status_code == 200, second_page.text
        second_payload = second_page.json()
        assert len(second_payload["items"]) == 1
        assert second_payload["meta"]["page"] == 2
        assert second_payload["items"][0]["name"].startswith(prefix)