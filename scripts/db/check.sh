#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source scripts/lib/sister_env.sh
sister_load_env "$ENV_NAME"

if command -v psql >/dev/null 2>&1; then
  psql "$SISTER_DATABASE_URL" -v ON_ERROR_STOP=1 -c "SELECT current_database() AS database, current_user AS user_name;"
  psql "$SISTER_DATABASE_URL" -v ON_ERROR_STOP=1 -c "SELECT extversion AS pgvector_version FROM pg_extension WHERE extname = 'vector';"
elif command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
  docker exec "$SISTER_DB_CONTAINER" psql -U sister -d sister -v ON_ERROR_STOP=1 -c "SELECT current_database() AS database, current_user AS user_name;"
  docker exec "$SISTER_DB_CONTAINER" psql -U sister -d sister -v ON_ERROR_STOP=1 -c "SELECT extversion AS pgvector_version FROM pg_extension WHERE extname = 'vector';"
elif command -v podman >/dev/null 2>&1 && podman ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
  podman exec "$SISTER_DB_CONTAINER" psql -U sister -d sister -v ON_ERROR_STOP=1 -c "SELECT current_database() AS database, current_user AS user_name;"
  podman exec "$SISTER_DB_CONTAINER" psql -U sister -d sister -v ON_ERROR_STOP=1 -c "SELECT extversion AS pgvector_version FROM pg_extension WHERE extname = 'vector';"
else
  echo "No psql client found and no running ${SISTER_DB_CONTAINER} container found." >&2
  echo "Run ./scripts/db/up.sh ${SISTER_ENV} first, or install psql." >&2
  exit 1
fi
