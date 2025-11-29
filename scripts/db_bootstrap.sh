#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
cd "$ROOT_DIR"

poetry install --no-interaction --no-root
poetry run alembic upgrade head
poetry run python scripts/create_admin_user.py
