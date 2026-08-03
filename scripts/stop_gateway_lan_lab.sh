#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run/gateway"

stop_pid() {
  local pid_file="$1"
  local expected="$2"
  [[ -f "$pid_file" ]] || return 0
  local pid
  pid="$(cat "$pid_file")"
  [[ "$pid" =~ ^[0-9]+$ ]] || { echo "invalid PID file: $pid_file" >&2; exit 1; }
  if kill -0 "$pid" >/dev/null 2>&1; then
    local command
    command="$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null || true)"
    [[ "$command" == *"$expected"* ]] || { echo "PID points to an unrelated process: $pid" >&2; exit 1; }
    kill "$pid"
    for _ in $(seq 1 50); do
      kill -0 "$pid" >/dev/null 2>&1 || break
      sleep 0.1
    done
    kill -0 "$pid" >/dev/null 2>&1 && { echo "process $pid did not stop" >&2; exit 1; }
  fi
  rm -f "$pid_file"
}

stop_pid "$RUN_DIR/haproxy.pid" haproxy
stop_pid "$RUN_DIR/lan-sisterd.pid" sisterd
rm -f "$RUN_DIR/sisterd.sock" "$RUN_DIR/haproxy.sock"
echo "lan gateway stopped"
