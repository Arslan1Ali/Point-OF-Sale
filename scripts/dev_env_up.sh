#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Allow additional args to pass through to docker compose
if [[ $# -gt 0 ]]; then
  docker compose -f docker-compose.dev.yml up --build "$@"
else
  docker compose -f docker-compose.dev.yml up --build
fi
