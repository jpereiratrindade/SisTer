#!/usr/bin/env bash

sister_compose_available() {
  command -v podman-compose >/dev/null 2>&1 \
    || command -v docker-compose >/dev/null 2>&1 \
    || command -v docker >/dev/null 2>&1
}

sister_compose() {
  if command -v podman-compose >/dev/null 2>&1; then
    podman-compose -f compose.yml "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f compose.yml "$@"
  elif command -v docker >/dev/null 2>&1; then
    docker compose -f compose.yml "$@"
  else
    echo "podman-compose, docker-compose or docker compose is required" >&2
    return 1
  fi
}
