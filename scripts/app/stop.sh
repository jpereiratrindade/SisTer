#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="$ROOT_DIR/.run/sisterd-${ENV_NAME}.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No sisterd PID file for ${ENV_NAME}."
  exit 0
fi

PID="$(cat "$PID_FILE")"
if [[ -n "$PID" ]] && kill -0 "$PID" >/dev/null 2>&1; then
  kill "$PID"
  echo "Stopped sisterd ${ENV_NAME} with PID ${PID}."
else
  echo "sisterd ${ENV_NAME} was not running."
fi

rm -f "$PID_FILE"
