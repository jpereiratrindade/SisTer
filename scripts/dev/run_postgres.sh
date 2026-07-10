#!/usr/bin/env bash
set -euo pipefail

if command -v podman-compose >/dev/null 2>&1; then
  podman-compose -f compose.yml up -d sister-db
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f compose.yml up -d sister-db
elif command -v docker >/dev/null 2>&1; then
  docker compose -f compose.yml up -d sister-db
else
  echo "podman-compose, docker-compose or docker compose is required" >&2
  exit 1
fi

cat <<'MSG'
PostgreSQL/PostGIS/pgvector requested.

Use:
  export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:5432/sister'

Check:
  ./build/apps/sisterctl/sisterctl db-check

Apply/reapply migration:
  ./build/apps/sisterctl/sisterctl db-migrate
MSG
