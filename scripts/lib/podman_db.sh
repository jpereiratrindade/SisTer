#!/usr/bin/env bash

sister_podman_image() {
  podman build -t sister-pgvector:17 -f docker/db/Dockerfile .
}

sister_podman_up() {
  sister_podman_image
  podman volume create "$SISTER_DB_VOLUME" >/dev/null
  podman run -d \
    --name "$SISTER_DB_CONTAINER" \
    --replace \
    -e POSTGRES_DB=sister \
    -e POSTGRES_USER=sister \
    -e POSTGRES_PASSWORD=sister \
    -p "127.0.0.1:${SISTER_DB_PORT}:5432" \
    -v "${SISTER_DB_VOLUME}:/var/lib/postgresql/data" \
    -v "${PWD}/storage/migrations:/docker-entrypoint-initdb.d:ro,Z" \
    --health-cmd='pg_isready -U sister -d sister' \
    --health-interval=10s \
    --health-timeout=5s \
    --health-retries=5 \
    sister-pgvector:17
  sister_podman_wait
}

sister_podman_down() {
  if podman container exists "$SISTER_DB_CONTAINER"; then
    podman stop "$SISTER_DB_CONTAINER" >/dev/null || true
  fi
}

sister_podman_destroy() {
  if podman container exists "$SISTER_DB_CONTAINER"; then
    podman rm -f "$SISTER_DB_CONTAINER" >/dev/null || true
  fi
  if podman volume exists "$SISTER_DB_VOLUME"; then
    podman volume rm "$SISTER_DB_VOLUME" >/dev/null
  fi
}

sister_podman_wait() {
  local status
  local attempt

  for attempt in $(seq 1 30); do
    status="$(podman inspect --format '{{.State.Health.Status}}' "$SISTER_DB_CONTAINER" 2>/dev/null || true)"
    if [[ "$status" == "healthy" ]]; then
      return 0
    fi
    sleep 1
  done

  echo "Container ${SISTER_DB_CONTAINER} did not become healthy." >&2
  podman logs "$SISTER_DB_CONTAINER" >&2 || true
  return 1
}
