# Lead Engineer Quick Checklist

Use this list as a pre-flight before starting any multi-slice initiative. It complements `.github/copilot-instructions.md`.

## Planning
- [ ] Review `NEXT_STEPS.md` to confirm sequencing (catalog → inventory → sales → customers → returns → purchasing).
- [ ] Identify dependent migrations and ensure corresponding Alembic scripts exist (`backend/alembic/versions/`).
- [ ] Align with desktop client owners on DTO changes; plan updates under `desktop_client/` in the same PR.
- [ ] Surface infra needs (docker-compose, secrets, queues) with Ops before implementation starts.

## Implementation
- [ ] Touch domain first (`app/domain/...`), then ports (`app/application/*/ports.py`), repositories, use cases, and finally routers/schemas.
- [ ] Enforce optimistic locking/versioning on mutable aggregates; verify repositories update `version` columns.
- [ ] Record `InventoryMovement` entries for any stock-changing workflow (sales, returns, purchases, adjustments).
- [ ] Emit `DomainEvent`s for flows that future reporting/async jobs will materialize.

## Quality gates
- [ ] Unit tests for domain/use cases (pytest mark async where needed); reuse fixtures from `tests/unit/`.
- [ ] Integration tests under `tests/integration/api/` covering happy path + failure edge cases.
- [ ] Run `poetry run pytest`, `poetry run ruff check .`, and `poetry run mypy .` before pushing.
- [ ] If migrations changed, sanity-check with `poetry run alembic upgrade head` and update test fixtures accordingly.

## Release prep
- [ ] Update `.github/copilot-instructions.md` when patterns or conventions shift.
- [ ] Document new env vars or config changes in `README.md` / `.env.example`.
- [ ] Validate container build path (`docker/Dockerfile`, `docker/entrypoint.sh`) if runtime behavior changed.
- [ ] Capture a smoke run (API + critical flows) and note trace IDs/log output for observability.
