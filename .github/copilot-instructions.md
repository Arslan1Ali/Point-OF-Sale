# Retail POS AI Playbook
## Project Surfaces
- `backend/` serves the FastAPI + SQLAlchemy API; `desktop_client/` is a PySimpleGUI MVVM shell that speaks to it.
- Poetry manages both projects; environment overrides come from `.env` / `.env.local` consumed by `app/core/settings.py`.
- Default DB URL is async SQLite (`sqlite+aiosqlite:///./dev.db`); use `postgresql+asyncpg://` when targeting Postgres.

## Backend Architecture
- Layers: `app/domain` (entities/value objects + ULIDs), `app/application` (ports + use cases), `app/infrastructure` (SQLAlchemy/adapters), `app/api` (routers + DTOs).
- Repository protocols live in `app/application/*/ports.py`; SQLAlchemy adapters sit in `app/infrastructure/db/repositories/*` and map to ORM models under `/models`.
- Async session factory is defined in `app/infrastructure/db/session.py`; the FastAPI dependency commits or rolls back per request.
- Structlog JSON logging is wired in `app/core/logging.py`; bind `trace_id` in request-scoped logs so downstream consumers stay correlated.
- Domain exceptions inherit `DomainError` and are translated by `DomainErrorMiddleware` into JSON responses with trace IDs.
- Pagination helpers (`app/shared/pagination.py`) provide the `meta` block expected by list endpoints.

## Domain Conventions
- IDs are ULIDs (`app/domain/common/identifiers.py`); avoid incremental IDs in new code or migrations.
- Monetary values flow through `Money` (Decimal rounding, no negatives) before persistence.
- Aggregates often mix in `EventRecorderMixin`; pull events in use cases before handing them to future dispatchers.
- Optimistic locking uses a `version` field mirrored between domain objects and SQLAlchemy models—increment it inside domain methods.

## API & Workflows
- Keep `app/api/routers/*` handlers thin: resolve dependencies, call a use case, shape the response with Pydantic schema from `app/api/schemas/*`.
- Catalog: product import use cases (`queue_`, `process_`, `retry_`, `get_*`) orchestrate `ProductImportJob` + `ProductImportItem`; preserve `errors` lists for desktop visibility.
- Inventory + sales flows rely on `InventoryMovement` records so `StockLevel.from_movements` stays the single source of truth.
- Returns and purchases reuse sales invariants; prefer extending shared domain logic over new bespoke aggregates.
- Auth tokens come from `app/application/auth/use_cases`; Argon2 password hashing lives in `app/infrastructure/auth/password_hasher.py` and token issuing in `token_provider.py`.

## Testing & Tooling
- Boot backend with `cd backend; poetry install; poetry run uvicorn app.api.main:app --reload` (structlog prints JSON to stdout).
- `tests/conftest.py` runs Alembic migrations once per session; async fixtures require `@pytest.mark.asyncio`.
- Primary checks: `poetry run pytest`, `poetry run ruff check .`, `poetry run mypy .` (strict mode configured in `pyproject.toml`).
- Integration suites under `tests/integration/api/` exercise routers against the async session; unit suites favour domain/service fakes.
- New migrations belong in `alembic/versions`; keep script paths relative as shown in `alembic/env.py` so CI resolves correctly.
- Full CI expectations live in `docs/ci-pipeline.md`; mirror those steps locally with `scripts/check_all.sh` before opening PRs.

## Desktop Client
- MVVM layout: views in `desktop_client/views/windows/`, view models in `desktop_client/view_models/`, API client in `desktop_client/core/api_client.py`.
- Install with `py -m poetry install --no-root`; launch via `py -m poetry run python -m desktop_client.app` after the backend is up.
- Login stores tokens then issues `/api/v1/products` fetches; align DTOs with backend schemas whenever fields shift.

## Deployment & Ops
- Docker image (`docker/Dockerfile`) installs Poetry; hook migrations in `docker/entrypoint.sh` before starting Uvicorn.
- Structured logging + future tracing expect `trace_id` propagation—bind context when spawning background tasks or schedulers.
- Track roadmap and cross-team agreements in `NEXT_STEPS.md`; update it when infra or sequencing assumptions change.
- Postgres rollout steps live in `backend/docs/postgres-migration.md`; follow it when switching from the default SQLite DSN.
- Logging & health expectations are documented in `docs/observability.md`; consult it before adding new background tasks or log formats.
- Local Docker Compose stack (`docker-compose.dev.yml`) plus helper scripts under `scripts/` bring up backend + Postgres + Redis for dev; keep them in sync with manual setup docs when adjusting services or ports.
- `.pre-commit-config.yaml` runs ruff, mypy, and the unit test subset via Poetry; keep parity with CI when adding new quality gates.
- CI adds Bandit and pip-audit security scans; ensure new dependencies stay compatible and update exclusions as needed.
