#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${1:-dev}"

args=(--environment "$ENV_NAME")
if [[ "${SISTER_SUBSYSTEMS_STRICT:-0}" == "1" ]]; then
  args+=(--strict)
fi

exec python3 "$ROOT_DIR/scripts/subsystems/ensure.py" "${args[@]}"
