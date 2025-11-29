# Postgres Migration Runbook

This guide standardizes how we switch the backend from the default SQLite DSN to Postgres in local and CI environments.

## Prerequisites
- Postgres 14+ reachable at `localhost:5432` (or adjust credentials accordingly).
- Database owner (e.g. `postgres`) with privileges to create the `retail_pos` database.
- Environment variables exported or defined in `.env.local`.
- When using Docker Compose, the container initializes with `--encoding=UTF8 --locale=en_US.UTF-8`. Adjust `POSTGRES_INITDB_ARGS` if your locale requirements differ.

```env
DATABASE_URL=postgresql+asyncpg://postgres:1234@localhost:5432/retail_pos
```

> ℹ️  The async driver (`+asyncpg`) is required for runtime. Alembic auto-converts it to a sync URL when applying migrations.

## Database Bootstrapping
1. Create the database if it does not exist:
   ```powershell
   $env:PGPASSWORD = "1234"
   psql -h localhost -U postgres -c "CREATE DATABASE retail_pos;"
   ```
2. Apply migrations:
   ```powershell
   cd backend
   poetry install
   poetry run alembic upgrade head
   ```
   > 💡 Alternatively, from the repository root run `./scripts/dev_env_up.sh` (or `.ps1`) to spin up Postgres + API via Docker Compose; migrations run automatically on container start.
   >
   > Or run `./scripts/db_bootstrap.sh` / `.ps1` to install dependencies, apply migrations, and ensure the admin user exists in one step.
3. Seed admin user (migration `0012_seed_admin_user` runs automatically). Credentials:
   - Email: `admin@retailpos.com`
   - Password: `AdminPass123!`
   - Admin lifecycle endpoints exposed under `/api/v1/auth/users/{id}/...` require these credentials for initial access.

## Rollback Procedure
- To revert the last migration set:
  ```powershell
  poetry run alembic downgrade -1
  ```
- To reseed the admin user after a downgrade/upgrade cycle:
  ```powershell
  poetry run alembic downgrade 0011_create_purchases_tables
  poetry run alembic upgrade head
  ```

## Verification Checklist
- `poetry run pytest` (ensures Alembic fixtures apply cleanly against Postgres).
- `poetry run ruff check .` and `poetry run mypy .` still succeed.
- Run `scripts/check_all.sh` (bash) or `scripts/check_all.ps1` (PowerShell) for a one-liner covering the checks above plus Alembic SQL dry run.
- `poetry run uvicorn app.api.main:app --reload` and `GET /health` returns `200`.
- Run a smoke auth + product flow using the desktop client or `tests/integration/api/test_products_api.py`.

Document issues and connection overrides in `NEXT_STEPS.md` so downstream teams stay in sync.
