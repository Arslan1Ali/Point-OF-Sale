from __future__ import annotations

import asyncio
import io
import json
from datetime import datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import app
from app.domain.auth.entities import UserRole
from tests.integration.api.helpers import create_user_and_login

CSV_TEMPLATE = """name,sku,retail_price,purchase_price,currency,category_id
{rows}
"""


async def _register_and_login(
    async_session,
    client: AsyncClient,
    email: str | None = None,
    password: str = "Secretp@ss1",
    *,
    role: UserRole = UserRole.MANAGER,
) -> str:
    actual_email = email or f"user_{uuid4().hex[:6]}@example.com"
    return await create_user_and_login(async_session, client, actual_email, password, role)


@pytest.mark.asyncio
async def test_import_requires_authentication():
    csv_body = CSV_TEMPLATE.format(rows="Widget,SKU123,10.00,5.00,USD,")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_body.encode("utf-8")), "text/csv")},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "unauthorized"
        assert body["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_import_validates_and_creates_job(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    sku = f"SKU{uuid4().hex[:8].upper()}"
    csv_body = CSV_TEMPLATE.format(rows=f"Widget,{sku},10.00,5.00,USD,")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_body.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 202, resp.text
        payload = resp.json()
        assert payload["status"] == "completed"
        assert payload["total_rows"] == 1
        assert payload["processed_rows"] == 1
        assert payload["error_count"] == 0
        job_id = payload["id"]

        check = await client.get(
            f"/api/v1/products/import/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert check.status_code == 200, check.text
        retrieved = check.json()
        assert retrieved["id"] == job_id
        assert retrieved["status"] == "completed"
        assert retrieved["processed_rows"] == 1
        assert retrieved["error_count"] == 0

        products = await client.get(
            "/api/v1/products",
            params={"search": "Widget"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert products.status_code == 200
        data = products.json()
        assert any(item["sku"] == sku for item in data["items"])


@pytest.mark.asyncio
async def test_import_marks_conflicts_and_records_errors(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    sku = f"SKU{uuid4().hex[:8].upper()}"
    csv_body = CSV_TEMPLATE.format(rows=f"Widget,{sku},10.00,5.00,USD,")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        create_resp = await client.post(
            "/api/v1/products",
            json={
                "name": "Existing",
                "sku": sku,
                "retail_price": "12.00",
                "purchase_price": "8.00",
                "currency": "USD",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201, create_resp.text

        resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_body.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 202, resp.text
        payload = resp.json()
        assert payload["status"] == "failed"
        assert payload["error_count"] == 1
        assert payload["processed_rows"] == 1
        conflict_message = f"Row 1: SKU '{sku}' already exists"
        assert payload["errors"] == [conflict_message]

        job_id = payload["id"]
        check = await client.get(
            f"/api/v1/products/import/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert check.status_code == 200
        retrieved = check.json()
        assert retrieved["status"] == "failed"
        assert retrieved["error_count"] == 1
        assert retrieved["processed_rows"] == 1
        assert retrieved["errors"] == [conflict_message]


@pytest.mark.asyncio
async def test_import_rejects_invalid_csv(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    csv_body = "name,sku\nWidget,SKU123"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_body.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        payload = resp.json()
        assert payload["code"] == "validation_error"
        assert payload["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_get_import_job_items_returns_detail(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    sku = f"SKU{uuid4().hex[:8].upper()}"
    csv_body = CSV_TEMPLATE.format(rows=f"Widget,{sku},10.00,5.00,USD,")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_body.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 202
        job_id = resp.json()["id"]

        detail = await client.get(
            f"/api/v1/products/import/{job_id}/items",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert detail.status_code == 200, detail.text
        payload = detail.json()
        assert payload["id"] == job_id
        assert payload["status"] == "completed"
        assert payload["processed_rows"] == 1
        assert payload["error_count"] == 0
        assert payload["items"]
        assert payload["items"][0]["status"] == "completed"
        assert payload["items"][0]["row_number"] == 1
        assert payload["items"][0]["payload"]["sku"] == sku
        assert payload["items"][0]["error_message"] is None
        assert payload["meta"] == {"page": 1, "limit": 20, "total": 1, "pages": 1}


@pytest.mark.asyncio
async def test_get_import_job_items_supports_pagination_and_status(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    existing_sku = f"SKU{uuid4().hex[:8].upper()}"
    new_sku = f"SKU{uuid4().hex[:8].upper()}"
    csv_body = CSV_TEMPLATE.format(
        rows="\n".join(
            [
                f"Widget,{existing_sku},10.00,5.00,USD,",
                f"WidgetTwo,{new_sku},15.00,7.50,USD,",
            ]
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)

        create_resp = await client.post(
            "/api/v1/products",
            json={
                "name": "Existing",
                "sku": existing_sku,
                "retail_price": "12.00",
                "purchase_price": "8.00",
                "currency": "USD",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201

        resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_body.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 202, resp.text
        job_id = resp.json()["id"]

        failed_only = await client.get(
            f"/api/v1/products/import/{job_id}/items",
            params={"status": "failed"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert failed_only.status_code == 200
        failed_payload = failed_only.json()
        assert failed_payload["meta"]["total"] == 1
        assert len(failed_payload["items"]) == 1
        assert failed_payload["items"][0]["status"] == "failed"

        second_page = await client.get(
            f"/api/v1/products/import/{job_id}/items",
            params={"page": 2, "limit": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert second_page.status_code == 200
        second_payload = second_page.json()
        assert second_payload["meta"] == {"page": 2, "limit": 1, "total": 2, "pages": 2}
        assert len(second_payload["items"]) == 1
        assert second_payload["items"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_get_import_job_items_not_found(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        missing_job_id = "01NOTFOUNDJOB0000000000000"
        resp = await client.get(
            f"/api/v1/products/import/{missing_job_id}/items",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "not_found"
        assert body["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_get_import_status_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/products/import/status")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "unauthorized"
        assert body["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_get_import_status_returns_summary(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    sku_success = f"SKU{uuid4().hex[:8].upper()}"
    sku_failure = f"SKU{uuid4().hex[:8].upper()}"
    csv_success = CSV_TEMPLATE.format(rows=f"Widget,{sku_success},10.00,5.00,USD,")
    csv_failure = CSV_TEMPLATE.format(rows=f"Widget,{sku_failure},10.00,5.00,USD,")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)

        baseline = await client.get(
            "/api/v1/products/import/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert baseline.status_code == 200
        before = baseline.json()

        success_resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_success.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert success_resp.status_code == 202, success_resp.text
        success_id = success_resp.json()["id"]

        create_resp = await client.post(
            "/api/v1/products",
            json={
                "name": "Existing",
                "sku": sku_failure,
                "retail_price": "12.00",
                "purchase_price": "8.00",
                "currency": "USD",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201, create_resp.text

        failure_resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_failure.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert failure_resp.status_code == 202, failure_resp.text
        failure_payload = failure_resp.json()
        assert failure_payload["status"] == "failed"
        failure_id = failure_payload["id"]

        summary_resp = await client.get(
            "/api/v1/products/import/status",
            params={"limit": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert summary_resp.status_code == 200, summary_resp.text
        summary = summary_resp.json()

        assert summary["total_jobs"] == before["total_jobs"] + 2
        assert summary["completed"] == before["completed"] + 1
        assert summary["failed"] == before["failed"] + 1
        assert summary["errors"] == before["errors"] + failure_payload["error_count"]
        assert summary["pending"] == before["pending"]
        assert summary["queued"] == before["queued"]
        assert summary["processing"] == before["processing"]

        assert len(summary["last_jobs"]) == 2
        returned_ids = [job["id"] for job in summary["last_jobs"]]
        assert returned_ids[0] == failure_id
        assert success_id in returned_ids


@pytest.mark.asyncio
async def test_stream_import_status_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/products/import/stream")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "unauthorized"
        assert body["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_stream_import_status_emits_events(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    sku = f"SKU{uuid4().hex[:8].upper()}"
    csv_body = CSV_TEMPLATE.format(rows=f"Widget,{sku},10.00,5.00,USD,")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=None) as client:
        token = await _register_and_login(async_session, client, unique_email)

        await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_body.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )

        params = {"poll_interval": 0.5, "limit": 1}
        headers = {"Authorization": f"Bearer {token}"}
        async with client.stream("GET", "/api/v1/products/import/stream", params=params, headers=headers) as response:
            assert response.status_code == 200
            content_type = response.headers.get("content-type", "")
            assert content_type.startswith("text/event-stream")
            assert response.headers.get("cache-control") == "no-cache"
            assert response.headers.get("x-accel-buffering") == "no"

            lines = response.aiter_lines()

            async def _next_data_line() -> str:
                while True:
                    line = await asyncio.wait_for(lines.__anext__(), timeout=3)
                    if line:
                        return line

            data_line = await _next_data_line()
            assert data_line.startswith("data: ")
            payload = json.loads(data_line.removeprefix("data: ").strip())
            assert payload["total_jobs"] >= 1
            assert "last_jobs" in payload

        # Stream context closed without hanging


@pytest.mark.asyncio
async def test_list_import_jobs_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/products/import")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "unauthorized"
        assert body["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_list_import_jobs_supports_filters_and_pagination(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    sku_success = f"SKU{uuid4().hex[:8].upper()}"
    sku_failure = f"SKU{uuid4().hex[:8].upper()}"
    csv_success = CSV_TEMPLATE.format(rows=f"Widget,{sku_success},10.00,5.00,USD,")
    csv_failure = CSV_TEMPLATE.format(rows=f"Widget,{sku_failure},10.00,5.00,USD,")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)

        baseline_resp = await client.get(
            "/api/v1/products/import",
            params={"limit": 50},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert baseline_resp.status_code == 200
        baseline = baseline_resp.json()
        baseline_total = baseline["meta"]["total"]

        success_resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_success.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert success_resp.status_code == 202, success_resp.text
        success_id = success_resp.json()["id"]

        create_resp = await client.post(
            "/api/v1/products",
            json={
                "name": "Existing",
                "sku": sku_failure,
                "retail_price": "12.00",
                "purchase_price": "8.00",
                "currency": "USD",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201, create_resp.text

        failure_resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_failure.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert failure_resp.status_code == 202, failure_resp.text
        failure_payload = failure_resp.json()
        assert failure_payload["status"] == "failed"
        failure_id = failure_payload["id"]

        list_resp = await client.get(
            "/api/v1/products/import",
            params={"limit": 10},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200
        payload = list_resp.json()
        assert payload["meta"]["total"] == baseline_total + 2
        assert payload["items"]
        ids = [item["id"] for item in payload["items"]]
        assert success_id in ids
        assert failure_id in ids
        assert payload["items"][0]["id"] == failure_id
        assert payload["items"][0]["status"] == "failed"

        failed_resp = await client.get(
            "/api/v1/products/import",
            params={"status": "failed", "limit": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert failed_resp.status_code == 200
        failed_payload = failed_resp.json()
        assert failed_payload["items"]
        assert all(item["status"] == "failed" for item in failed_payload["items"])
        assert any(item["id"] == failure_id for item in failed_payload["items"])

        paged_resp = await client.get(
            "/api/v1/products/import",
            params={"page": 2, "limit": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert paged_resp.status_code == 200
        paged_payload = paged_resp.json()
        assert paged_payload["meta"]["page"] == 2
        assert paged_payload["meta"]["limit"] == 1
        assert paged_payload["meta"]["total"] == baseline_total + 2


@pytest.mark.asyncio
async def test_retry_import_job_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/products/import/01NOTFOUNDJOB0000000000000/retry")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "unauthorized"
        assert body["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_retry_import_job_not_found(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)
        resp = await client.post(
            "/api/v1/products/import/01NOTFOUNDJOB0000000000000/retry",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "not_found"
        assert body["trace_id"] == resp.headers.get("X-Trace-Id")


@pytest.mark.asyncio
async def test_retry_import_job_reprocesses_failed_job(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    sku = f"SKU{uuid4().hex[:8].upper()}"
    csv_body = CSV_TEMPLATE.format(rows=f"Widget,{sku},10.00,5.00,USD,")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)

        create_resp = await client.post(
            "/api/v1/products",
            json={
                "name": "Existing",
                "sku": sku,
                "retail_price": "12.00",
                "purchase_price": "8.00",
                "currency": "USD",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201, create_resp.text

        failed_resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_body.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert failed_resp.status_code == 202, failed_resp.text
        failed_payload = failed_resp.json()
        assert failed_payload["status"] == "failed"
        job_id = failed_payload["id"]
        initial_updated_at = datetime.fromisoformat(failed_payload["updated_at"])

        retry_resp = await client.post(
            f"/api/v1/products/import/{job_id}/retry",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert retry_resp.status_code == 202, retry_resp.text
        retry_payload = retry_resp.json()
        assert retry_payload["id"] == job_id
        assert retry_payload["status"] == "failed"
        assert retry_payload["error_count"] == failed_payload["error_count"]
        assert retry_payload["errors"] == failed_payload["errors"]
        assert retry_payload["processed_rows"] == failed_payload["processed_rows"]
        retry_updated_at = datetime.fromisoformat(retry_payload["updated_at"])
        assert retry_updated_at > initial_updated_at


@pytest.mark.asyncio
async def test_retry_import_job_rejects_non_failed_job(async_session):
    unique_email = f"user_{uuid4().hex[:6]}@example.com"
    sku = f"SKU{uuid4().hex[:8].upper()}"
    csv_body = CSV_TEMPLATE.format(rows=f"Widget,{sku},10.00,5.00,USD,")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register_and_login(async_session, client, unique_email)

        success_resp = await client.post(
            "/api/v1/products/import",
            files={"file": ("import.csv", io.BytesIO(csv_body.encode("utf-8")), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert success_resp.status_code == 202, success_resp.text
        job_id = success_resp.json()["id"]
        assert success_resp.json()["status"] == "completed"

        retry_resp = await client.post(
            f"/api/v1/products/import/{job_id}/retry",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert retry_resp.status_code == 400
        body = retry_resp.json()
        assert body["code"] == "validation_error"
        message = body.get("message") or body.get("detail") or ""
        assert "failed import jobs" in message.lower()
