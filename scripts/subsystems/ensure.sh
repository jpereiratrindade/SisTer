#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${1:-dev}"
if [[ $# -gt 0 ]]; then
  shift
fi

args=(--environment "$ENV_NAME")

exec python3 "$ROOT_DIR/scripts/subsystems/ensure.py" "${args[@]}" "$@"
