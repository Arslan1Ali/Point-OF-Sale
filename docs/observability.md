# Observability Playbook

## Logging
- Structured logging via `structlog` writes JSON to stdout.
- `DomainErrorMiddleware` binds a `trace_id` per request and ensures it flows through response headers.
- Use `structlog.get_logger(__name__)` and avoid bare `print` statements.
- For background work (e.g., product import scheduler) bind a trace ID with `structlog.contextvars.bind_contextvars(trace_id=...)` and clear it afterward.
- Helpers in `app/core/logging.py`:
  - `bind_trace_id(trace_id: str | None = None) -> str`
  - `reset_context()`

### Admin Action Audit Trail
- Every admin mutation (deactivate, activate, role change, password reset) produces an `admin_action_logs` record.
- Query via `GET /api/v1/auth/admin-actions` with optional filters (`actor_user_id`, `target_user_id`, `action`, `start`, `end`).
- Desktop operators can review the same data using the “Admin Actions” dialog in the PySimpleGUI client; pagination defaults to 20 rows.
- Include the `trace_id` column when correlating log entries with structured API logs.

## Metrics & Health
- `/health` endpoint returns `{"status":"ok"}` and should be wired into uptime checks.
- Plan to expose basic metrics (Prometheus) in Phase 2; current placeholder flag `ENABLE_TRACING` in settings.

## Troubleshooting Workflow
1. Reproduce the issue and capture the `X-Trace-Id` header.
2. Search logs for the matching `trace_id` to gather context across API + background logs.
3. Confirm database changes via Alembic timestamps; each migration logs application progress.
4. When scheduler logs show `product_import_job_failed`, cross-reference import job records via `/api/v1/products/import/{job_id}`.

Update this document as we roll out tracing (OpenTelemetry) and metrics exporters.