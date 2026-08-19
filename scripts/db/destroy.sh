#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-test}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source scripts/lib/sister_env.sh
source scripts/lib/compose.sh
source scripts/lib/podman_db.sh

sister_load_env "$ENV_NAME"
if [[ -n "${SISTER_DB_DATA_DIR:-}" ]]; then
  if command -v podman >/dev/null 2>&1; then
    sister_podman_destroy
  else
    echo "SISTER_DB_DATA_DIR requires podman for this incremental contract" >&2
    exit 1
  fi
elif sister_compose_available; then
  sister_compose down -v
elif command -v podman >/dev/null 2>&1; then
  sister_podman_destroy
else
  echo "podman-compose, docker-compose, docker compose or podman is required" >&2
  exit 1
fi
sister_print_env
if [[ -n "${SISTER_DB_DATA_DIR:-}" ]]; then
  echo "Destroyed database container for ${SISTER_ENV}; bind-mounted data was preserved."
else
  echo "Destroyed database container and volume for ${SISTER_ENV}."
fi
