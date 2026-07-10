#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=../lib/sister_env.sh
source scripts/lib/sister_env.sh
# shellcheck source=../lib/compose.sh
source scripts/lib/compose.sh
# shellcheck source=../lib/podman_db.sh
source scripts/lib/podman_db.sh

sister_load_env "$ENV_NAME"
if sister_compose_available; then
  sister_compose up -d sister-db
elif command -v podman >/dev/null 2>&1; then
  sister_podman_up
else
  echo "podman-compose, docker-compose, docker compose or podman is required" >&2
  exit 1
fi
sister_print_env
