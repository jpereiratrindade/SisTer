#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
if [[ ! "$ENV_NAME" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "stop.sh: invalid environment name" >&2
  exit 3
fi
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="$ROOT_DIR/.run/sisterd-${ENV_NAME}.pid"
EXECUTABLE="$ROOT_DIR/build/apps/sisterd/sisterd"
IDENTITY_TOOL="$ROOT_DIR/scripts/app/process_identity.py"

if [[ ! -e "$PID_FILE" && ! -L "$PID_FILE" ]]; then
  echo "No sisterd PID file for ${ENV_NAME}."
  exit 0
fi

set +e
PID="$(python3 "$IDENTITY_TOOL" terminate \
  --pid-file "$PID_FILE" \
  --environment "$ENV_NAME" \
  --executable "$EXECUTABLE")"
VALIDATION_CODE=$?
set -e

if [[ $VALIDATION_CODE -eq 4 ]]; then
  echo "sisterd ${ENV_NAME} was not running."
  rm -f "$PID_FILE"
  exit 0
fi
if [[ $VALIDATION_CODE -ne 0 ]]; then
  echo "Refusing to stop an unverified process for ${ENV_NAME}." >&2
  exit 3
fi

STOPPED=0
for _ in $(seq 1 40); do
  set +e
  python3 "$IDENTITY_TOOL" validate \
    --pid-file "$PID_FILE" \
    --environment "$ENV_NAME" \
    --executable "$EXECUTABLE" >/dev/null 2>&1
  CURRENT_CODE=$?
  set -e
  if [[ $CURRENT_CODE -ne 0 ]]; then
    STOPPED=1
    break
  fi
  sleep 0.25
done
if [[ $STOPPED -ne 1 ]]; then
  echo "sisterd ${ENV_NAME} with PID ${PID} did not stop." >&2
  exit 1
fi

rm -f "$PID_FILE"
echo "Stopped sisterd ${ENV_NAME} with PID ${PID}."
