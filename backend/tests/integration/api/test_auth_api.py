import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import app
from app.domain.auth.entities import UserRole
from app.infrastructure.db.repositories.user_repository import UserRepository
from tests.integration.api.helpers import create_user, login_as


@pytest.mark.asyncio
async def test_register_and_login(async_session, monkeypatch):
    # Use real app with test client
    transport = ASGITransport(app=app)
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # register
        r = await ac.post("/api/v1/auth/register", json={"email": unique_email, "password": "password123"})
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["email"] == unique_email

        # login
        r2 = await ac.post("/api/v1/auth/login", json={"email": unique_email, "password": "password123"})
        assert r2.status_code == 200, r2.text
        tokens = r2.json()
        assert "access_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "X-Trace-Id" in r2.headers


@pytest.mark.asyncio
async def test_register_duplicate_email_conflict(async_session, monkeypatch):
    transport = ASGITransport(app=app)
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.post("/api/v1/auth/register", json={"email": unique_email, "password": "password123"})
        assert first.status_code == 201

        second = await ac.post("/api/v1/auth/register", json={"email": unique_email, "password": "password123"})
        assert second.status_code == 409
        payload = second.json()
        assert payload["code"] == "conflict"
        assert payload["detail"] == "email already registered"
        assert payload["trace_id"]
        assert second.headers.get("X-Trace-Id") == payload["trace_id"]


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_unauthorized(async_session, monkeypatch):
    transport = ASGITransport(app=app)
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={"email": unique_email, "password": "password123"})
        assert reg.status_code == 201

        login = await ac.post("/api/v1/auth/login", json={"email": unique_email, "password": "wrongpass"})
        assert login.status_code == 401
        payload = login.json()
        assert payload["code"] == "unauthorized"
        assert payload["detail"] == "invalid credentials"
        assert payload["trace_id"] == login.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_refresh_rotates_and_rejects_reuse(async_session, monkeypatch):
    transport = ASGITransport(app=app)
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # register + login to obtain initial refresh token
        reg = await ac.post("/api/v1/auth/register", json={"email": unique_email, "password": "password123"})
        assert reg.status_code == 201, reg.text

        login = await ac.post("/api/v1/auth/login", json={"email": unique_email, "password": "password123"})
        assert login.status_code == 200, login.text
        initial_tokens = login.json()
        original_refresh = initial_tokens["refresh_token"]

        # rotate refresh token
        refresh_resp = await ac.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})
        assert refresh_resp.status_code == 200, refresh_resp.text
        rotated = refresh_resp.json()
        rotated_refresh = rotated["refresh_token"]
        assert rotated_refresh != original_refresh

        # old token reuse should fail
        reuse_resp = await ac.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})
        assert reuse_resp.status_code == 401
        reuse_payload = reuse_resp.json()
        assert reuse_payload["code"] in {"invalid_token", "token_revoked"}
        assert reuse_payload["trace_id"] == reuse_resp.headers.get("X-Trace-Id")

        # new token should still succeed (second rotation)
        second_refresh = await ac.post("/api/v1/auth/refresh", json={"refresh_token": rotated_refresh})
        assert second_refresh.status_code == 200, second_refresh.text
        second_tokens = second_refresh.json()
        assert "access_token" in second_tokens
        assert second_tokens["refresh_token"] != rotated_refresh


@pytest.mark.asyncio
async def test_me_returns_authenticated_user(async_session, monkeypatch):
    transport = ASGITransport(app=app)
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={"email": unique_email, "password": "password123"})
        assert reg.status_code == 201

        login = await ac.post("/api/v1/auth/login", json={"email": unique_email, "password": "password123"})
        assert login.status_code == 200
        tokens = login.json()

        me = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert me.status_code == 200, me.text
        payload = me.json()
        assert payload["email"] == unique_email
        assert payload["id"]


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(async_session, monkeypatch):
    transport = ASGITransport(app=app)
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={"email": unique_email, "password": "password123"})
        assert reg.status_code == 201

        login = await ac.post("/api/v1/auth/login", json={"email": unique_email, "password": "password123"})
        assert login.status_code == 200
        tokens = login.json()
        refresh_token = tokens["refresh_token"]

        logout = await ac.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert logout.status_code == 204, logout.text

        reuse = await ac.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert reuse.status_code == 401
        reuse_payload = reuse.json()
        assert reuse_payload["code"] in {"invalid_token", "refresh_token_not_found", "token_revoked"}


@pytest.mark.asyncio
async def test_logout_all_revokes_all_tokens(async_session, monkeypatch):
    transport = ASGITransport(app=app)
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={"email": unique_email, "password": "password123"})
        assert reg.status_code == 201

        login = await ac.post("/api/v1/auth/login", json={"email": unique_email, "password": "password123"})
        assert login.status_code == 200
        first_tokens = login.json()

        refresh = await ac.post("/api/v1/auth/refresh", json={"refresh_token": first_tokens["refresh_token"]})
        assert refresh.status_code == 200
        second_tokens = refresh.json()

        logout_all_resp = await ac.post(
            "/api/v1/auth/logout-all",
            headers={"Authorization": f"Bearer {second_tokens['access_token']}"},
        )
        assert logout_all_resp.status_code == 204, logout_all_resp.text

        reuse_first = await ac.post("/api/v1/auth/refresh", json={"refresh_token": first_tokens["refresh_token"]})
        reuse_second = await ac.post("/api/v1/auth/refresh", json={"refresh_token": second_tokens["refresh_token"]})

        assert reuse_first.status_code == 401
        assert reuse_second.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_manage_user_lifecycle(async_session, monkeypatch):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_token = await login_as(async_session, ac, UserRole.ADMIN, email_prefix="admin")
        target_email = f"managed_{uuid.uuid4().hex[:8]}@example.com"
        initial_password = "Initial123!"
        await create_user(async_session, target_email, initial_password, UserRole.CASHIER)
        await async_session.commit()
        repo = UserRepository(async_session)
        target = await repo.get_by_email(target_email)
        assert target is not None
        user_id = target.id
        expected_version = target.version
        headers = {"Authorization": f"Bearer {admin_token}"}

        deactivate = await ac.post(
            f"/api/v1/auth/users/{user_id}/deactivate",
            json={"expected_version": expected_version},
            headers=headers,
        )
        assert deactivate.status_code == 200, deactivate.text
        payload = deactivate.json()
        assert payload["active"] is False
        assert payload["version"] == expected_version + 1
        expected_version = payload["version"]

        double_deactivate = await ac.post(
            f"/api/v1/auth/users/{user_id}/deactivate",
            json={"expected_version": expected_version},
            headers=headers,
        )
        assert double_deactivate.status_code == 400
        assert double_deactivate.json()["code"] == "user_already_inactive"

        activate = await ac.post(
            f"/api/v1/auth/users/{user_id}/activate",
            json={"expected_version": expected_version},
            headers=headers,
        )
        assert activate.status_code == 200, activate.text
        payload = activate.json()
        assert payload["active"] is True
        expected_version = payload["version"]

        change_role = await ac.post(
            f"/api/v1/auth/users/{user_id}/role",
            json={"expected_version": expected_version, "role": UserRole.MANAGER.value},
            headers=headers,
        )
        assert change_role.status_code == 200, change_role.text
        payload = change_role.json()
        assert payload["role"] == UserRole.MANAGER.value
        expected_version = payload["version"]

        new_password = "N3wP@ssw0rd!"
        reset = await ac.post(
            f"/api/v1/auth/users/{user_id}/password",
            json={"expected_version": expected_version, "new_password": new_password},
            headers=headers,
        )
        assert reset.status_code == 200, reset.text
        payload = reset.json()
        expected_version = payload["version"]

        login_old = await ac.post(
            "/api/v1/auth/login",
            json={"email": target_email, "password": initial_password},
        )
        assert login_old.status_code == 401

        login_new = await ac.post(
            "/api/v1/auth/login",
            json={"email": target_email, "password": new_password},
        )
        assert login_new.status_code == 200, login_new.text
        assert "access_token" in login_new.json()

        await async_session.commit()
        updated = await repo.get_by_id(user_id)
        assert updated is not None
        assert updated.active is True
        assert updated.role == UserRole.MANAGER
        assert updated.version == expected_version

        list_response = await ac.get(
            "/api/v1/auth/admin-actions",
            headers=headers,
            params={"target_user_id": user_id, "limit": 50},
        )
        assert list_response.status_code == 200, list_response.text
        log_payload = list_response.json()
        assert log_payload["meta"]["total"] == 4
        assert [item["action"] for item in log_payload["items"]] == [
            "user.reset_password",
            "user.change_role",
            "user.activate",
            "user.deactivate",
        ]
        assert log_payload["items"][0]["details"]["password_reset"] is True

        filtered_response = await ac.get(
            "/api/v1/auth/admin-actions",
            headers=headers,
            params={"target_user_id": user_id, "action": "user.activate"},
        )
        assert filtered_response.status_code == 200, filtered_response.text
        filtered_payload = filtered_response.json()
        assert filtered_payload["meta"]["total"] == 1
        assert filtered_payload["items"][0]["action"] == "user.activate"


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_users(async_session, monkeypatch):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        manager_token = await login_as(async_session, ac, UserRole.MANAGER, email_prefix="manager")
        target_email = f"staff_{uuid.uuid4().hex[:8]}@example.com"
        await create_user(async_session, target_email, "Initial123!", UserRole.CASHIER)
        await async_session.commit()
        repo = UserRepository(async_session)
        target = await repo.get_by_email(target_email)
        assert target is not None

        response = await ac.post(
            f"/api/v1/auth/users/{target.id}/deactivate",
            json={"expected_version": target.version},
            headers={"Authorization": f"Bearer {manager_token}"},
        )

        assert response.status_code == 403
        payload = response.json()
        assert payload["code"] == "insufficient_role"

        auditor_token = await login_as(async_session, ac, UserRole.ADMIN, email_prefix="auditor")
        audit_response = await ac.get(
            "/api/v1/auth/admin-actions",
            headers={"Authorization": f"Bearer {auditor_token}"},
            params={"target_user_id": target.id},
        )
        assert audit_response.status_code == 200, audit_response.text
        assert audit_response.json()["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_admin_actions_supports_pagination(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_token = await login_as(async_session, ac, UserRole.ADMIN, email_prefix="auditor")
        target_email = f"audit_{uuid.uuid4().hex[:8]}@example.com"
        await create_user(async_session, target_email, "Initial123!", UserRole.CASHIER)
        await async_session.commit()
        repo = UserRepository(async_session)
        target = await repo.get_by_email(target_email)
        assert target is not None
        headers = {"Authorization": f"Bearer {admin_token}"}

        async def _post(path: str, payload: dict[str, Any]) -> None:
            response = await ac.post(path, json=payload, headers=headers)
            assert response.status_code == 200, response.text

        expected_version = target.version
        await _post(
            f"/api/v1/auth/users/{target.id}/deactivate",
            {"expected_version": expected_version},
        )
        expected_version += 1
        await _post(
            f"/api/v1/auth/users/{target.id}/activate",
            {"expected_version": expected_version},
        )
        expected_version += 1
        await _post(
            f"/api/v1/auth/users/{target.id}/role",
            {"expected_version": expected_version, "role": UserRole.MANAGER.value},
        )
        expected_version += 1
        await _post(
            f"/api/v1/auth/users/{target.id}/password",
            {"expected_version": expected_version, "new_password": "N3wP@ssw0rd!"},
        )

        first_page = await ac.get(
            "/api/v1/auth/admin-actions",
            headers=headers,
            params={"target_user_id": target.id, "limit": 2},
        )
        assert first_page.status_code == 200, first_page.text
        first_payload = first_page.json()
        assert first_payload["meta"]["total"] >= 4
        assert first_payload["meta"]["pages"] >= 2
        assert len(first_payload["items"]) == 2

        second_page = await ac.get(
            "/api/v1/auth/admin-actions",
            headers=headers,
            params={"target_user_id": target.id, "limit": 2, "page": 2},
        )
        assert second_page.status_code == 200, second_page.text
        second_payload = second_page.json()
        assert len(second_payload["items"]) >= 1
        assert second_payload["meta"]["page"] == 2


@pytest.mark.asyncio
async def test_admin_can_list_users_with_filters(async_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_token = await login_as(async_session, ac, UserRole.ADMIN, email_prefix="auditor")
        cashier_email = f"cashier_{uuid.uuid4().hex[:8]}@example.com"
        manager_email = f"manager_{uuid.uuid4().hex[:8]}@example.com"
        await create_user(async_session, cashier_email, "Secret123!", UserRole.CASHIER)
        await create_user(async_session, manager_email, "Secret123!", UserRole.MANAGER)
        await async_session.commit()

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await ac.get(
            "/api/v1/auth/users",
            headers=headers,
            params={"limit": 10, "search": "manager", "role": UserRole.MANAGER.value},
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["meta"]["total"] >= 1
        assert all(item["role"] == UserRole.MANAGER.value for item in payload["items"])
        assert any(item["email"] == manager_email for item in payload["items"])