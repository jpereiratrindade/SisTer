#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

source scripts/lib/sister_env.sh
sister_load_env "$ENV_NAME"
PORT="${2:-$SISTER_APP_PORT}"

cmake -S . -B build
cmake --build build --target sisterd

mkdir -p .run
scripts/app/stop.sh "$ENV_NAME" >/dev/null || true

LOG_FILE="$ROOT_DIR/.run/sisterd-${ENV_NAME}.log"
PID_FILE="$ROOT_DIR/.run/sisterd-${ENV_NAME}.pid"

if command -v setsid >/dev/null 2>&1; then
  setsid env SISTER_DATABASE_URL="$SISTER_DATABASE_URL" ./build/apps/sisterd/sisterd "$PORT" web >"$LOG_FILE" 2>&1 &
else
  SISTER_DATABASE_URL="$SISTER_DATABASE_URL" nohup ./build/apps/sisterd/sisterd "$PORT" web >"$LOG_FILE" 2>&1 &
fi
PID="$!"
echo "$PID" > "$PID_FILE"

for _ in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! kill -0 "$PID" >/dev/null 2>&1; then
  echo "sisterd failed to start. Log:" >&2
  cat "$LOG_FILE" >&2
  exit 1
fi

echo "sisterd ${ENV_NAME} running with PID ${PID}."
echo "Local:   http://127.0.0.1:${PORT}"
if command -v hostname >/dev/null 2>&1; then
  IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [[ -n "${IP:-}" ]]; then
    echo "Network: http://${IP}:${PORT}"
  fi
fi
echo "Log:     ${LOG_FILE}"
