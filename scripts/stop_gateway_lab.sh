#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/.run/gateway/haproxy.pid"
STATS_SOCKET="$ROOT_DIR/.run/gateway/haproxy.sock"

if [[ ! -f "$PID_FILE" ]]; then
  rm -f "$STATS_SOCKET"
  echo "gateway lab is not running"
  exit 0
fi
gateway_pid="$(cat "$PID_FILE")"
if [[ ! "$gateway_pid" =~ ^[0-9]+$ ]]; then
  echo "invalid gateway PID file" >&2
  exit 1
fi
if kill -0 "$gateway_pid" >/dev/null 2>&1; then
  gateway_command="$(tr '\0' ' ' <"/proc/$gateway_pid/cmdline" 2>/dev/null || true)"
  if [[ "$gateway_command" != *haproxy* ]]; then
    echo "gateway PID points to an unrelated live process; refusing to signal it" >&2
    exit 1
  fi
  kill "$gateway_pid"
  for _ in $(seq 1 50); do
    if ! kill -0 "$gateway_pid" >/dev/null 2>&1; then
      break
    fi
    sleep 0.1
  done
  if kill -0 "$gateway_pid" >/dev/null 2>&1; then
    echo "gateway lab process $gateway_pid did not stop" >&2
    exit 1
  fi
fi
rm -f "$PID_FILE" "$STATS_SOCKET"
echo "gateway lab stopped"
