#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ $# -gt 0 ]]; then
  docker compose -f docker-compose.dev.yml down "$@"
else
  docker compose -f docker-compose.dev.yml down --volumes
fi
