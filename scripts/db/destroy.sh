#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-test}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source scripts/lib/sister_env.sh
source scripts/lib/compose.sh
source scripts/lib/podman_db.sh

sister_load_env "$ENV_NAME"
if sister_compose_available; then
  sister_compose down -v
elif command -v podman >/dev/null 2>&1; then
  sister_podman_destroy
else
  echo "podman-compose, docker-compose, docker compose or podman is required" >&2
  exit 1
fi
sister_print_env
echo "Destroyed database container and volume for ${SISTER_ENV}."
