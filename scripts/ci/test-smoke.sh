#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SISTERD="$ROOT/build/apps/sisterd/sisterd"
[[ -x "$SISTERD" ]] || {
  echo "smoke test requires the tested sisterd artifact; run scripts/run_quality.sh first" >&2
  exit 1
}

RUNTIME="$(mktemp -d "${TMPDIR:-/tmp}/sister-smoke.XXXXXX")"
PORT="$(python3 - <<'PY'
import socket
with socket.socket() as listener:
    listener.bind(("127.0.0.1", 0))
    print(listener.getsockname()[1])
PY
)"
PID=""

cleanup() {
  if [[ -n "$PID" ]] && kill -0 "$PID" >/dev/null 2>&1; then
    kill "$PID" >/dev/null 2>&1 || true
    wait "$PID" >/dev/null 2>&1 || true
  fi
  rm -rf "$RUNTIME"
}
trap cleanup EXIT

env \
  SISTER_ENV=development \
  SISTER_BIND_HOST=127.0.0.1 \
  SISTER_AUTH_FILE="$RUNTIME/auth.tsv" \
  SISTER_DATABASE_URL= \
  SISTER_COOKIE_SECURE=false \
  SISTER_ENABLE_REFERENCE_SUBSYSTEM=false \
  "$SISTERD" "$PORT" "$ROOT/web" >"$RUNTIME/sisterd.log" 2>&1 &
PID="$!"

READY=0
for _ in $(seq 1 50); do
  if curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  kill -0 "$PID" >/dev/null 2>&1 || break
  sleep 0.1
done
if [[ $READY -ne 1 ]]; then
  echo "isolated sisterd did not become ready" >&2
  cat "$RUNTIME/sisterd.log" >&2
  exit 1
fi

"$ROOT/scripts/app/smoke.sh" "$PORT"
