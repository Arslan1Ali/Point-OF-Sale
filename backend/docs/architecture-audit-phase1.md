# Backend Architecture Audit – Phase 1 (2025-10-19)

## Executive Summary
- The FastAPI backend follows a clean architecture split (api → application → domain → infrastructure) with SQLAlchemy adapters and Alembic migrations already in place.
- Core cross-cutting concerns (settings, structlog JSON logging, domain error middleware) exist, but production hardening is incomplete (debug defaults, permissive CORS, static secrets).
- Feature domains (auth, catalog, inventory, sales, returns, purchases, suppliers, customers) expose endpoints via dedicated routers; coverage leans toward catalog/auth with reusable pagination helpers.
- Testing relies on Alembic-driven SQLite; local automation depends on Poetry yet the tool is absent from the environment, highlighting DevEx gaps that block repeatable validation.

## Current Architecture Inventory

### Runtime & Configuration
- **Framework**: FastAPI app factory in `app/api/main.py`; lifespan hook reserved for future startup tasks.
- **Middleware**: `DomainErrorMiddleware` binds a `trace_id`, translates `DomainError` subclasses, and responds with JSON plus `X-Trace-Id` headers.
- **Logging**: `app/core/logging.py` wires structlog with JSON output; contextvars supply per-request metadata.
- **Settings**: `Settings` (pydantic-settings) loads from `.env` / `.env.local`. Defaults currently favor development (`DEBUG=True`, `DATABASE_URL=sqlite+aiosqlite:///./dev.db`, wildcard CORS, `JWT_SECRET_KEY="CHANGE_ME"`).
- **Observability flags**: `ENABLE_TRACING` placeholder (unused yet) indicates intent for future instrumentation.

### Persistence & Infrastructure
- **SQLAlchemy**: Async engine/session factory in `app/infrastructure/db/session.py`; `async_sessionmaker` used across repositories. Engine echoes SQL when `DEBUG=True`.
- **Migrations**: Alembic configured (`alembic.ini`, `alembic/env.py`) with versioned scripts 0001–0014 covering catalog, auth, inventory, sales, returns, purchases, admin logs.
- **Repositories**: Infrastructure layer under `app/infrastructure/db/repositories/` implements protocols from `app/application/*/ports.py` (e.g., `SqlAlchemyProductRepository`, `UserRepository`). Optimistic locking enforced via `version` filters.
- **Auth adapters**: `TokenProvider` (PyJWT) and `PasswordHasher` (passlib Argon2) satisfy application ports; refresh tokens tracked in DB via repositories/models.

### Domain & Application Layers
- **Domain modeling**: ULID identifiers (`app/domain/common/identifiers.py`), value objects (`Money`), aggregates for catalog, auth, inventory, sales, returns, purchases, suppliers, customers. Domain mutators often raise `ValueError` instead of custom exceptions.
- **Application services**: Use cases live under `app/application/*/use_cases`; they accept protocol dependencies for repositories/schedulers/dispatchers and return domain objects or DTO-style results.
- **Events**: `EventRecorderMixin` scaffolding present but event dispatch pipelines not yet implemented.

### API Surface (v1)
- **Auth (`/api/v1/auth`)**: register, login, refresh, logout (single/all), current user, admin-only user lifecycle (activate/deactivate/change role/reset password) and admin action logs with pagination.
- **Products (`/api/v1/products`)**: CRUD-lite (create, update, deactivate), list with filters, stock & inventory movements, CSV import workflow (queue, status, job detail, retry) using immediate scheduler backing.
- **Categories (`/api/v1/categories`)**: Category management endpoints (listing, creation, updates) backing product catalog hierarchies (details in router file).
- **Inventory (`/inventory` subroutes)**: Embedded within product router for movement recording/listing and stock lookup.
- **Sales/Returns/Purchases/Suppliers/Customers Routers**: Endpoint sets for transactional flows (create sale/return/purchase, list records, manage suppliers/customers); leverage shared pagination + role guards.
- **Health**: `/health` unauthenticated probe.

### Quality & Tooling Signals
- **Testing**: `tests/conftest.py` applies Alembic migrations once, exposing async session fixtures. Integration suites cover API routers (auth, catalog, inventory, sales, returns, purchases). Domain/application units exist for critical aggregates.
- **Automation**: `pyproject.toml` defines Ruff, mypy (strict, tests excluded), pytest, bandit, pip-audit. Scripts under `scripts/` wrap preflight checks.
- **Current run state**: `poetry run pytest -q` failed locally because `poetry` command is missing—developer environment bootstrap instructions are not automated.

## Observed Risks & Gaps
| Priority | Area | Finding | Impact | Suggested Action |
|----------|------|---------|--------|------------------|
| High | Configuration | Default `.env` values leave `DEBUG=True`, wildcard CORS, hard-coded `JWT_SECRET_KEY` and SQLite DSN. | Production deployment would expose secrets, verbose SQL logs, and insecure cross-origin access. | Externalize secrets via env/KeyVault, enforce `DEBUG=False`, restricted CORS, and mandate Postgres DSN per `docs/postgres-migration.md`. |
| High | Security | Token validation relies on static symmetric key without rotation strategy; refresh token revocation handled but lacks device metadata/audit correlation. | Compromised key invalidates security posture; difficult to investigate session anomalies. | Introduce key management SOP (rotation window, JWKS or Azure Key Vault), augment `RefreshToken` schema with device/client info, link admin action logs to token events. |
| High | Import Processing | `ImmediateImportScheduler` executes imports inline during request lifecycle. Large CSVs block responders and risk timeout. | Degrades UX and scalability; prevents horizontal scaling and background retries. | Implement asynchronous execution (Celery/Redis per declared dependencies), persist job queue metadata, add progress notifications. |
| Medium | Domain Consistency | Many domain methods raise `ValueError` instead of bespoke `DomainError` subclasses. | Error translation middleware cannot surface structured codes/messages; input validation bleeds into infrastructure. | Replace raw `ValueError` with domain-specific exceptions mapped to API errors, update tests accordingly. |
| Medium | Observability | Trace ID binding happens for HTTP requests only; background tasks and import scheduler supply ad-hoc IDs. No metrics/tracing exported despite settings flag. | Limited ability to correlate cross-service workflows or monitor SLIs. | Extend logging helpers to background contexts, integrate OpenTelemetry (metrics/traces) aligned with `docs/observability.md`. |
| Medium | Dev Experience | Poetry absent on contributor workstation; README lacks quick-start verification checklist. | Onboarding friction and inconsistent lint/test execution. | Add bootstrap script/checklist (`scripts/dev_env_up.*`), document prerequisite installs, consider pinned Poetry via `install-poetry.py`. |
| Low | Dependency Footprint | `celery`, `redis`, `tenacity` declared but unused in code; risk of drift. | Bloated image size, potential security CVEs without benefit. | Either wire planned background processing (see import backlog) or slim dependencies and document roadmap. |
| Low | Config Flexibility | Settings do not expose API docs toggles, allowed origins list, or rate limiting parameters needed for enterprise rollouts. | Additional controls will be needed before go-live. | Expand `Settings` schema with deployment-grade knobs and document defaults in env samples. |

## Backlog for Phase 2 and Beyond
1. **Production Configuration Hardening**
   - Implement secure defaults in `app/core/settings.py`, update `.env.example`, and document environment-specific overrides.
   - Enforce minimal CORS, add secret rotation guidance, and wire Postgres readiness per `docs/postgres-migration.md`.
2. **Security & Authentication Enhancements**
   - Introduce key rotation / JWKS endpoint, expand refresh token metadata, and align admin audit logs with token lifecycle events.
   - Add automated tests covering token expiry, revocation, and role-based guards across routers.
3. **Asynchronous Import Pipeline**
   - Replace `ImmediateImportScheduler` with Celery/Redis-backed queue; emit progress events and reconcile retry semantics.
   - Update API contracts to expose job progress and ensure idempotent replays.
4. **Domain Error Refinement**
   - Refactor domain entities to raise typed `DomainError` subclasses; adjust middleware mappings and validation schemas.
   - Expand unit tests to assert error codes and HTTP responses.
5. **Observability & Operations**
   - Implement tracing/metrics exporters (OpenTelemetry) leveraging `trace_id`, add structured health checks, integrate with logging sinks.
   - Update runbooks in `docs/observability.md` and `NEXT_STEPS.md` to reflect instrumentation rollout.
6. **Developer Experience Improvements**
   - Provide reproducible setup scripts (Poetry install, env templates, DB bootstrap). Ensure `scripts/check_all.*` run in CI and locally.
   - Add Makefile/PowerShell wrappers for common tasks on Windows and *nix.
7. **Dependency Hygiene**
   - Audit unused dependencies; either implement planned features (task queues, caching) or remove to reduce attack surface.

_Phase 1 deliverable complete. Ready to proceed with Phase 2 once priorities are confirmed._
