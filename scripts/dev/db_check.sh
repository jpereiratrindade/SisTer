#!/usr/bin/env bash
set -euo pipefail

DB_URL="${SISTER_DATABASE_URL:-postgresql://sister:sister@localhost:5432/sister}"

if command -v psql >/dev/null 2>&1; then
  psql "$DB_URL" -v ON_ERROR_STOP=1 -c "SELECT current_database() AS database, current_user AS user_name;"
  psql "$DB_URL" -v ON_ERROR_STOP=1 -c "SELECT postgis_version() AS postgis_version;"
  psql "$DB_URL" -v ON_ERROR_STOP=1 -c "SELECT extversion AS pgvector_version FROM pg_extension WHERE extname = 'vector';"
elif command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -qx 'sister-db'; then
  docker exec sister-db psql -U sister -d sister -v ON_ERROR_STOP=1 -c "SELECT current_database() AS database, current_user AS user_name;"
  docker exec sister-db psql -U sister -d sister -v ON_ERROR_STOP=1 -c "SELECT postgis_version() AS postgis_version;"
  docker exec sister-db psql -U sister -d sister -v ON_ERROR_STOP=1 -c "SELECT extversion AS pgvector_version FROM pg_extension WHERE extname = 'vector';"
else
  echo "No psql client found and no running sister-db container found." >&2
  echo "Run ./scripts/dev/run_postgres.sh first, or install psql." >&2
  exit 1
fi
