#!/usr/bin/env bash
set -euo pipefail

# Runs the same checks as CI for quick local validation.

if [[ -z "${DATABASE_URL:-}" ]]; then
	echo "DATABASE_URL is not set. See backend/docs/postgres-migration.md for setup." >&2
	exit 1
fi

pushd "$(dirname "$0")/../backend" >/dev/null
poetry install --no-interaction --no-root
poetry run ruff check .
poetry run mypy .
poetry run bandit -q -r app
poetry run pip-audit --strict
poetry run pytest --cov=app --cov-report=term --cov-report=xml --cov-fail-under=80
poetry run alembic upgrade head --sql >/tmp/alembic.sql
popd >/dev/null

echo "✔ All checks completed. Alembic SQL written to /tmp/alembic.sql"