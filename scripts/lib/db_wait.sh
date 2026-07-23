#!/usr/bin/env bash

sister_db_ready() {
  if command -v pg_isready >/dev/null 2>&1; then
    pg_isready -d "$SISTER_DATABASE_URL" >/dev/null 2>&1
  elif command -v docker >/dev/null 2>&1 \
    && docker ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
    docker exec "$SISTER_DB_CONTAINER" pg_isready -U sister -d sister >/dev/null 2>&1
  elif command -v podman >/dev/null 2>&1 \
    && podman ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
    podman exec "$SISTER_DB_CONTAINER" pg_isready -U sister -d sister >/dev/null 2>&1
  else
    return 1
  fi
}

sister_wait_for_db() {
  local attempt

  for attempt in $(seq 1 30); do
    if sister_db_ready; then
      return 0
    fi
    sleep 1
  done

  echo "Database ${SISTER_DB_CONTAINER} did not become ready on port ${SISTER_DB_PORT}." >&2
  return 1
}
