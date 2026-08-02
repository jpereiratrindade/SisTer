#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run/gateway"
PID_FILE="$RUN_DIR/haproxy.pid"
LOG_FILE="$RUN_DIR/haproxy.log"
CONFIG_FILE="$RUN_DIR/haproxy.cfg"

: "${GATEWAY_HAPROXY_BIN:?GATEWAY_HAPROXY_BIN must be an absolute HAProxy 3.2 path}"
export GATEWAY_TLS_PEM="${GATEWAY_TLS_PEM:-$RUN_DIR/gateway-lab.pem}"
export GATEWAY_ALLOWED_HOST="${GATEWAY_ALLOWED_HOST:-sister-gateway.test}"
export GATEWAY_CANONICAL_HOST="${GATEWAY_CANONICAL_HOST:-$GATEWAY_ALLOWED_HOST}"

mkdir -p "$RUN_DIR"
chmod 700 "$RUN_DIR"
if [[ -f "$PID_FILE" ]]; then
  existing_pid="$(cat "$PID_FILE")"
  if [[ "$existing_pid" =~ ^[0-9]+$ ]] && kill -0 "$existing_pid" >/dev/null 2>&1; then
    existing_command="$(tr '\0' ' ' <"/proc/$existing_pid/cmdline" 2>/dev/null || true)"
    if [[ "$existing_command" != *haproxy* ]]; then
      echo "gateway lab PID file points to an unrelated live process; refusing to overwrite it" >&2
      exit 1
    fi
    echo "gateway lab is already running with PID $existing_pid" >&2
    exit 1
  fi
  rm -f "$PID_FILE"
fi

python3 "$ROOT_DIR/scripts/render_gateway_config.py" --output "$CONFIG_FILE"
"$ROOT_DIR/scripts/validate_gateway_config.sh" "$CONFIG_FILE"

"$GATEWAY_HAPROXY_BIN" -Ws -f "$CONFIG_FILE" >"$LOG_FILE" 2>&1 &
gateway_pid="$!"
printf '%s\n' "$gateway_pid" >"$PID_FILE"
chmod 600 "$PID_FILE" "$LOG_FILE"

for _ in $(seq 1 40); do
  if ! kill -0 "$gateway_pid" >/dev/null 2>&1; then
    echo "gateway lab failed to start; see $LOG_FILE" >&2
    rm -f "$PID_FILE"
    exit 1
  fi
  if timeout 1 openssl s_client -connect 127.0.0.1:8443 \
      -servername "$GATEWAY_ALLOWED_HOST" -tls1_3 \
      -CAfile "$RUN_DIR/ca-lab.crt" </dev/null >/dev/null 2>&1; then
    echo "gateway lab running with PID $gateway_pid on https://127.0.0.1:8443"
    exit 0
  fi
  sleep 0.1
done

kill "$gateway_pid" >/dev/null 2>&1 || true
wait "$gateway_pid" 2>/dev/null || true
rm -f "$PID_FILE"
echo "gateway lab did not become ready; see $LOG_FILE" >&2
exit 1
