#!/usr/bin/env bash
set -euo pipefail

alembic upgrade head || echo "Skipping migrations (placeholder)"
exec "$@"
