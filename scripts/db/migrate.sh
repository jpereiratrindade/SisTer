#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
MIGRATION="${2:-storage/migrations/001_init.sql}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source scripts/lib/sister_env.sh
sister_load_env "$ENV_NAME"

if [[ ! -f "$MIGRATION" ]]; then
  echo "Migration not found: $MIGRATION" >&2
  exit 1
fi

if command -v psql >/dev/null 2>&1; then
  psql "$SISTER_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$MIGRATION"
elif command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
  docker exec -i "$SISTER_DB_CONTAINER" psql -U sister -d sister -v ON_ERROR_STOP=1 < "$MIGRATION"
elif command -v podman >/dev/null 2>&1 && podman ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
  podman exec -i "$SISTER_DB_CONTAINER" psql -U sister -d sister -v ON_ERROR_STOP=1 < "$MIGRATION"
else
  echo "No psql client found and no running ${SISTER_DB_CONTAINER} container found." >&2
  echo "Run ./scripts/db/up.sh ${SISTER_ENV} first, or install psql." >&2
  exit 1
fi

echo "Migration applied to ${SISTER_ENV}: ${MIGRATION}"
