#!/usr/bin/env bash
set -euo pipefail

MIGRATION="${1:-storage/migrations/001_init.sql}"
DB_URL="${SISTER_DATABASE_URL:-postgresql://sister:sister@localhost:5432/sister}"

if [[ ! -f "$MIGRATION" ]]; then
  echo "Migration not found: $MIGRATION" >&2
  exit 1
fi

if command -v psql >/dev/null 2>&1; then
  psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$MIGRATION"
elif command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -qx 'sister-db'; then
  docker exec -i sister-db psql -U sister -d sister -v ON_ERROR_STOP=1 < "$MIGRATION"
else
  echo "No psql client found and no running sister-db container found." >&2
  echo "Run ./scripts/dev/run_postgres.sh first, or install psql." >&2
  exit 1
fi

echo "Migration applied: $MIGRATION"
