#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
if [[ ! "$ENV_NAME" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "serve.sh: invalid environment name" >&2
  exit 3
fi
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source scripts/lib/sister_env.sh
sister_load_env "$ENV_NAME"
PORT="${2:-$SISTER_APP_PORT}"
BUILD_MODE="${3:-build}"

case "$BUILD_MODE" in
  build)
    cmake -S . -B build
    cmake --build build --target sisterd
    ;;
  --no-build)
    if [[ ! -x ./build/apps/sisterd/sisterd ]]; then
      echo "sisterd tested artifact is missing; run the quality build first" >&2
      exit 1
    fi
    ;;
  *)
    echo "serve.sh: expected build or --no-build, got $BUILD_MODE" >&2
    exit 3
    ;;
esac

mkdir -p .run
scripts/app/stop.sh "$ENV_NAME" --core-only >/dev/null

LOG_FILE="$ROOT_DIR/.run/sisterd-${ENV_NAME}.log"
PID_FILE="$ROOT_DIR/.run/sisterd-${ENV_NAME}.pid"

SISTERD_ENV=(
  SISTER_ENV="$ENV_NAME"
  SISTER_DATABASE_URL="$SISTER_DATABASE_URL"
  SISTER_ENABLE_REFERENCE_SUBSYSTEM="${SISTER_ENABLE_REFERENCE_SUBSYSTEM:-false}"
  SISTER_REFERENCE_PORT="${SISTER_REFERENCE_PORT:-19001}"
  SISTER_INTERNAL_PROXY_TOKEN="${SISTER_INTERNAL_PROXY_TOKEN:-}"
)
if command -v setsid >/dev/null 2>&1; then
  setsid env "${SISTERD_ENV[@]}" ./build/apps/sisterd/sisterd "$PORT" web >"$LOG_FILE" 2>&1 &
else
  env "${SISTERD_ENV[@]}" nohup ./build/apps/sisterd/sisterd "$PORT" web >"$LOG_FILE" 2>&1 &
fi
PID="$!"
if ! python3 scripts/app/process_identity.py record \
  --pid-file "$PID_FILE" \
  --pid "$PID" \
  --environment "$ENV_NAME" \
  --executable "$ROOT_DIR/build/apps/sisterd/sisterd"; then
  kill -- "$PID" >/dev/null 2>&1 || true
  wait "$PID" >/dev/null 2>&1 || true
  exit 3
fi

READY=0
for _ in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  if ! kill -0 "$PID" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! kill -0 "$PID" >/dev/null 2>&1; then
  echo "sisterd failed to start. Log:" >&2
  scripts/app/stop.sh "$ENV_NAME" --core-only >/dev/null
  cat "$LOG_FILE" >&2
  exit 1
fi
if [[ $READY -ne 1 ]]; then
  echo "sisterd remained alive but did not become ready. Log:" >&2
  ./scripts/app/stop.sh "$ENV_NAME" --core-only >/dev/null
  cat "$LOG_FILE" >&2
  exit 1
fi

echo "sisterd ${ENV_NAME} running with PID ${PID}."
echo "Local:   http://127.0.0.1:${PORT}"
echo "Log:     ${LOG_FILE}"
