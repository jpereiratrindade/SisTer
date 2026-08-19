#!/usr/bin/env bash

sister_podman_image() {
  podman build -t sister-pgvector:17 -f docker/db/Dockerfile .
}

sister_podman_db_mount_source() {
  if [[ -n "${SISTER_DB_DATA_DIR:-}" ]]; then
    printf '%s\n' "$SISTER_DB_DATA_DIR"
  else
    printf '%s\n' "$SISTER_DB_VOLUME"
  fi
}

sister_podman_assert_bind_storage_identity() {
  [[ -n "${SISTER_DB_DATA_DIR:-}" ]] || return 0

  if ! podman container exists "$SISTER_DB_CONTAINER"; then
    return 0
  fi

  local actual_source
  local expected_source

  actual_source="$(
    podman inspect \
      --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Source}}{{end}}{{end}}' \
      "$SISTER_DB_CONTAINER" 2>/dev/null || true
  )"

  [[ -n "$actual_source" ]] || {
    echo "Refusing to touch ${SISTER_DB_CONTAINER}: database mount could not be identified." >&2
    return 1
  }

  expected_source="$(realpath -m -- "$SISTER_DB_DATA_DIR")"
  actual_source="$(realpath -m -- "$actual_source")"

  if [[ "$actual_source" != "$expected_source" ]]; then
    cat >&2 <<MSG
Refusing to touch ${SISTER_DB_CONTAINER}: storage identity mismatch.
  expected: ${expected_source}
  actual:   ${actual_source}
This protects an existing operational database from a development/candidate command.
MSG
    return 1
  fi
}

sister_podman_prepare_data_mount() {
  if [[ -n "${SISTER_DB_DATA_DIR:-}" ]]; then
    mkdir -p -- "$SISTER_DB_DATA_DIR"
    printf '%s\n' "${SISTER_DB_DATA_DIR}:/var/lib/postgresql/data:Z"
    return 0
  fi

  podman volume exists "$SISTER_DB_VOLUME" || \
    podman volume create "$SISTER_DB_VOLUME" >/dev/null

  printf '%s\n' "${SISTER_DB_VOLUME}:/var/lib/postgresql/data"
}

sister_podman_up() {
  local db_mount

  sister_podman_assert_bind_storage_identity || return $?
  sister_podman_image
  db_mount="$(sister_podman_prepare_data_mount)"

  podman run -d \
    --name "$SISTER_DB_CONTAINER" \
    --replace \
    -e POSTGRES_DB=sister \
    -e POSTGRES_USER=sister \
    -e POSTGRES_PASSWORD="${SISTER_DB_PASSWORD}" \
    -p "127.0.0.1:${SISTER_DB_PORT}:5432" \
    -v "$db_mount" \
    -v "${PWD}/storage/migrations:/docker-entrypoint-initdb.d:ro,Z" \
    --health-cmd='pg_isready -U sister -d sister' \
    --health-interval=10s \
    --health-timeout=5s \
    --health-retries=5 \
    sister-pgvector:17

  sister_podman_wait
}

sister_podman_down() {
  sister_podman_assert_bind_storage_identity || return $?

  if podman container exists "$SISTER_DB_CONTAINER"; then
    podman stop "$SISTER_DB_CONTAINER" >/dev/null || true
  fi
}

sister_podman_destroy() {
  sister_podman_assert_bind_storage_identity || return $?

  if podman container exists "$SISTER_DB_CONTAINER"; then
    podman rm -f "$SISTER_DB_CONTAINER" >/dev/null || true
  fi

  if [[ -n "${SISTER_DB_DATA_DIR:-}" ]]; then
    echo "Bind-mounted database data preserved at ${SISTER_DB_DATA_DIR}."
    return 0
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
