# Retail POS Backend (Python/FastAPI)

Initial clean architecture scaffold for the retail-only POS domain.

## Stack
- FastAPI / Uvicorn
- SQLAlchemy 2.0 (async) targeting Postgres (SQLite only used for legacy scaffolding)
- Pydantic v2 & pydantic-settings
- Poetry for dependency management
- Celery (future async jobs) & Redis (future cache/rate-limit)

## Layout (Early Stage)
```
app/
  core/        # cross-cutting concerns (config, logging, security)
  domain/      # pure domain model (entities, value objects, events)
  application/ # use cases / orchestrators
  infrastructure/ # adapters (db, repositories, external services)
  api/         # routers + schemas (no business logic)
  tests/       # unit/integration/e2e (added at root tests/ for now)
```

## Quick Start

### Prerequisites
- Install Poetry (`pipx install poetry` or `pip install --user poetry`).
- Ensure Postgres is available when not using the default SQLite dev DSN.

```bash
cp .env.example .env.local  # adjust credentials as needed
poetry install
poetry run uvicorn app.api.main:app --reload
```

Update `.env.local` with your trusted hosts and frontend origins. Staging/prod deployments must set
`ALLOWED_HOSTS`, `CORS_ORIGINS`, `DATABASE_URL`, and a strong `JWT_SECRET_KEY`; the settings module will
reject wildcard values in those environments.

#### Docker Compose Dev Stack

Alternatively, run the API + Postgres (and Redis placeholder) via Docker Compose from the repo root:

```bash
./scripts/dev_env_up.sh  # add -d to run detached
```

PowerShell equivalent:

```powershell
./scripts/dev_env_up.ps1
```

The stack exposes FastAPI on `http://localhost:8000` and Postgres on `localhost:5432`. Stop everything with `./scripts/dev_env_down.sh` or `./scripts/dev_env_down.ps1`.

Health endpoint: `GET /health`

### Database Migrations & Seeded Admin
- Configure `DATABASE_URL` in `.env.local` (see `backend/docs/postgres-migration.md`).
- Apply migrations with `alembic upgrade head` (or the equivalent virtualenv command).
- Default Postgres credentials for local setups: user `postgres`, password `1234`, database `retail_pos`.

When using Docker Compose, migrations are applied automatically on container start via `alembic upgrade head`.

To bootstrap (or re-bootstrap) the local database manually run:

```bash
./scripts/db_bootstrap.sh
```

PowerShell equivalent:

```powershell
./scripts/db_bootstrap.ps1
```
- Migration `0012_seed_admin_user` provisions an admin account on first run:
  - Email: `admin@retailpos.com`
  - Password: `AdminPass123!`
- If you previously ran migrations before 2025-10-10, run `alembic downgrade 0011` then `alembic upgrade head` to reseed with the updated email domain accepted by the API.
- Re-running migrations is idempotent; the seed only inserts the admin if it doesn't already exist.

### Run Tests
```bash
poetry run pytest -q  # requires DATABASE_URL to point at Postgres
```

### Lint & Type Check
```bash
poetry run ruff check .
poetry run mypy .
```

### Pre-commit Hooks
Install the hooks once, then they run automatically on `git commit`:

```bash
poetry run pip install pre-commit  # or install globally
pre-commit install
```

Hooks mirror CI: ruff, mypy, and the unit test suite (`tests/unit`). Run them on demand with `pre-commit run --all-files`.

### Security Scans
CI (and `scripts/check_all.*`) run Bandit and `pip-audit --strict`. You can execute them manually via:

```bash
poetry run bandit -q -r app
poetry run pip-audit --strict
```

## Current Implemented Slice
- Product domain entity (basic invariants)
- Create product use case (duplicate SKU guard)
- SQLAlchemy persistence (SQLite dev auto-create tables)
- FastAPI endpoints: POST /api/v1/products, GET /api/v1/products (pagination + search)
- Basic structured logging (structlog JSON)

## Immediate Next Steps (Backend)
1. Introduce repository port separation file (move protocol to dedicated interface module).
2. Implement proper Alembic migrations (replace auto create).
3. Add auth & user domain (JWT, password hashing Argon2id, roles scaffold).
4. Introduce domain events base + event dispatcher placeholder.
5. Add update/deactivate product use cases.
6. Implement optimistic locking (version check) on updates.
7. Add basic error taxonomy mapping (domain -> HTTP codes).

## Roadmap (High Level)
Phase 1: Auth & Users
Phase 2: Catalog Expansion (categories, bulk import)
Phase 3: Inventory Ledger & Stock projections
Phase 4: Sales Transaction Engine
Phase 5: Customers & History
Phase 6: Returns Module
Phase 7: Purchasing & Suppliers
Phase 8: Reporting + Async Jobs (Celery)
Phase 9: Alerts & Notifications
Phase 10: Hardening (observability, rate limit, security)

## Desktop Client (Future Parallel Work)
Will live under `desktop_client/` with PySimpleGUI, local SQLite cache, sync queue, MVVM style view_models.

## Configuration
Environment via `.env` or `.env.local` (start from `.env.example`). See `app/core/settings.py` for overridable keys.

## Deployment (Early Notes)
Container build provided in `docker/Dockerfile` (currently uses Poetry; no migrations run). Entry script will later invoke Alembic.

## API Reference (Incremental)
### List Products
`GET /api/v1/products`

Query Params:
| Name | Type | Default | Notes |
|------|------|---------|-------|
| page | int  | 1       | Page number (>=1) |
| limit | int | 20      | Items per page (<=100) |
| search | str | - | Case-insensitive partial match on name |
| category_id | str | - | Filter by category |
| active | bool | - | Filter active state |

Example Response:
```json
{
  "items": [
    {"id": "01HV...", "name": "Prod 1", "sku": "SKU1", "retail_price": "10.00", "purchase_price": "5.00", "category_id": null, "active": true}
  ],
  "meta": {"page":1, "limit":20, "total":57, "pages":3}
}
```

### List Admin Actions
`GET /api/v1/auth/admin-actions`

Query Params:
| Name | Type | Default | Notes |
|------|------|---------|-------|
| page | int | 1 | Page number (>=1) |
| limit | int | 20 | Items per page (<=100) |
| actor_user_id | str | - | Filter by actor (admin) user ID |
| target_user_id | str | - | Filter by target user ID |
| action | str | - | Filter by action (e.g. `user.activate`) |
| start | str | - | ISO8601 UTC start datetime filter |
| end | str | - | ISO8601 UTC end datetime filter |

Example Response:
```json
{
  "items": [
    {
      "id": "01HV...",
      "actor_user_id": "01HV...",
      "target_user_id": "01HX...",
      "action": "user.activate",
      "details": {"expected_version": 1, "resulting_version": 2},
      "trace_id": "abc123",
      "created_at": "2025-10-18T12:34:56.789Z"
    }
  ],
  "meta": {"page":1, "limit":20, "total":4, "pages":1}
}
```

- Admin-only endpoint; non-admin users receive HTTP 403.
- Supports pagination and filtering by actor, target, action, and date range.
- All datetimes are serialized in UTC ISO8601 format.

### List Users
`GET /api/v1/auth/users`

Query Params:
| Name | Type | Default | Notes |
|------|------|---------|-------|
| page | int | 1 | Page number (>=1) |
| limit | int | 20 | Items per page (<=100) |
| search | str | - | Case-insensitive partial match on email |
| role | str | - | Filter by role (`admin`, `manager`, `cashier`) |
| active | bool | - | Filter by active state |

Example Response:
```json
{
  "items": [
    {
      "id": "01HX...",
      "email": "manager@example.com",
      "role": "manager",
      "active": true,
      "version": 2
    }
  ],
  "meta": {"page":1, "limit":20, "total":12, "pages":1}
}
```

- Admin-only endpoint that powers desktop user management.
- Combine with mutation endpoints (`/auth/users/{id}/activate`, `/deactivate`, `/role`, `/password`) for full lifecycle control.

## Contributing
Use feature branches; run tests and lint before PR. Keep domain layer free from infrastructure imports.

---
This scaffold is intentionally minimal to enable iterative vertical slices.

Refer to overarching architecture plan in project discussion documentation.
