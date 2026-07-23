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
# shellcheck source=../lib/db_wait.sh
source scripts/lib/db_wait.sh

sister_load_env "$ENV_NAME"
if sister_compose_available; then
  if command -v podman-compose >/dev/null 2>&1 && command -v podman >/dev/null 2>&1 \
    && podman container exists "$SISTER_DB_CONTAINER"; then
    if [[ "$(podman inspect --format '{{.State.Running}}' "$SISTER_DB_CONTAINER")" == "true" ]]; then
      echo "Reusing running database container ${SISTER_DB_CONTAINER}."
    else
      podman rm "$SISTER_DB_CONTAINER" >/dev/null
      sister_compose up -d sister-db
    fi
  else
    sister_compose up -d sister-db
  fi
elif command -v podman >/dev/null 2>&1; then
  sister_podman_up
else
  echo "podman-compose, docker-compose, docker compose or podman is required" >&2
  exit 1
fi
sister_wait_for_db
sister_print_env
