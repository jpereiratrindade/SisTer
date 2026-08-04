#!/usr/bin/env bash
set -euo pipefail

allowed_project="${1:-${COMPOSE_PROJECT_NAME:-}}"
if [[ -z "$allowed_project" ]]; then
  echo "stop_unmanaged_sister_containers: missing allowed compose project" >&2
  exit 3
fi

if ! command -v podman >/dev/null 2>&1; then
  exit 0
fi

while IFS=$'\t' read -r name compose_project; do
  [[ -n "$name" && -n "$compose_project" ]] || continue
  [[ "$compose_project" == sister-* ]] || continue
  [[ "$compose_project" != "$allowed_project" ]] || continue
  podman stop "$name" >/dev/null || true
  echo "Stopped unmanaged SisTer-local container: $name ($compose_project)"
done < <(podman ps --format '{{.Names}}	{{.Label "com.docker.compose.project"}}')
