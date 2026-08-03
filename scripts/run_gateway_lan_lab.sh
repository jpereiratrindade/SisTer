#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run/gateway"
SISTERD_PID_FILE="$RUN_DIR/lan-sisterd.pid"
SISTERD_LOG_FILE="$RUN_DIR/lan-sisterd.log"
SISTERD_SOCKET="$RUN_DIR/sisterd.sock"
GATEWAY_PID_FILE="$RUN_DIR/haproxy.pid"

: "${GATEWAY_HAPROXY_BIN:?GATEWAY_HAPROXY_BIN must be an absolute HAProxy 3.2 path}"
: "${GATEWAY_LAN_ADDRESS:?GATEWAY_LAN_ADDRESS must be the laptop private IPv4 address}"
export GATEWAY_ALLOWED_HOST="${GATEWAY_ALLOWED_HOST:-sister-gateway.test}"
export GATEWAY_CANONICAL_HOST="${GATEWAY_CANONICAL_HOST:-$GATEWAY_ALLOWED_HOST}"
export GATEWAY_LISTEN_ADDRESS="$GATEWAY_LAN_ADDRESS"
export GATEWAY_TLS_PEM="${GATEWAY_TLS_PEM:-$RUN_DIR/gateway-lab.pem}"
export GATEWAY_UPSTREAM_SOCKET="$SISTERD_SOCKET"

mkdir -p "$RUN_DIR"
chmod 700 "$RUN_DIR"
if [[ -f "$SISTERD_PID_FILE" || -f "$GATEWAY_PID_FILE" ]]; then
  echo "lan gateway appears to be running; use scripts/stop_gateway_lan_lab.sh first" >&2
  exit 1
fi

source "$ROOT_DIR/scripts/lib/sister_env.sh"
sister_load_env test
"$ROOT_DIR/scripts/db/up.sh" test
"$ROOT_DIR/scripts/db/migrate.sh" test
cmake -S "$ROOT_DIR" -B "$ROOT_DIR/build"
cmake --build "$ROOT_DIR/build" --target sisterd --parallel
"$ROOT_DIR/scripts/create_gateway_lab_certificate.sh" "$GATEWAY_ALLOWED_HOST"

rm -f "$SISTERD_SOCKET"
launch_prefix=()
if command -v setsid >/dev/null 2>&1; then
  launch_prefix=(setsid)
fi

"${launch_prefix[@]}" env \
  SISTER_ENV=test \
  SISTER_LISTENER_MODE=systemd-unix \
  SISTER_ACTIVATED_SOCKET_PATH="$SISTERD_SOCKET" \
  SISTER_WEB_ROOT="$ROOT_DIR/web" \
  SISTER_AUTH_FILE="$RUN_DIR/auth-users.tsv" \
  SISTER_ENABLE_HTTP_BOOTSTRAP=false \
  SISTER_ENABLE_LEGACY_PROXY=false \
  SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY=false \
  SISTER_ENABLE_NEXO_SIGNED_INTEGRATION=false \
  SISTER_DATABASE_URL="$SISTER_DATABASE_URL" \
  python3 "$ROOT_DIR/scripts/app/socket_activation_lab.py" \
    "$SISTERD_SOCKET" "$ROOT_DIR/build/apps/sisterd/sisterd" \
    </dev/null >"$SISTERD_LOG_FILE" 2>&1 &
sisterd_pid="$!"
printf '%s\n' "$sisterd_pid" >"$SISTERD_PID_FILE"
chmod 600 "$SISTERD_PID_FILE" "$SISTERD_LOG_FILE"

for _ in $(seq 1 40); do
  if ! kill -0 "$sisterd_pid" >/dev/null 2>&1; then
    echo "lan sisterd failed to start; see $SISTERD_LOG_FILE" >&2
    rm -f "$SISTERD_PID_FILE"
    exit 1
  fi
  if [[ -S "$SISTERD_SOCKET" ]]; then
    break
  fi
  sleep 0.1
done
if [[ ! -S "$SISTERD_SOCKET" ]]; then
  echo "lan sisterd did not create its Unix socket; see $SISTERD_LOG_FILE" >&2
  exit 1
fi

export GATEWAY_TLS_PEM GATEWAY_ALLOWED_HOST GATEWAY_CANONICAL_HOST
python3 "$ROOT_DIR/scripts/render_gateway_config.py" --scope lan-lab --output "$RUN_DIR/haproxy.cfg"
"$ROOT_DIR/scripts/validate_gateway_config.sh" "$RUN_DIR/haproxy.cfg"

"${launch_prefix[@]}" "$GATEWAY_HAPROXY_BIN" -Ws -f "$RUN_DIR/haproxy.cfg" \
  </dev/null >"$RUN_DIR/haproxy.log" 2>&1 &
gateway_pid="$!"
printf '%s\n' "$gateway_pid" >"$GATEWAY_PID_FILE"
chmod 600 "$GATEWAY_PID_FILE" "$RUN_DIR/haproxy.log"

for _ in $(seq 1 50); do
  if ! kill -0 "$gateway_pid" >/dev/null 2>&1; then
    echo "lan gateway failed to start; see $RUN_DIR/haproxy.log" >&2
    exit 1
  fi
  if curl --silent --show-error --fail \
      --resolve "$GATEWAY_ALLOWED_HOST:8443:$GATEWAY_LAN_ADDRESS" \
      --cacert "$RUN_DIR/ca-lab.crt" \
      "https://$GATEWAY_ALLOWED_HOST:8443/api/health" >/dev/null 2>&1; then
    echo "lan gateway running on https://$GATEWAY_ALLOWED_HOST:8443"
    echo "LAN address: $GATEWAY_LAN_ADDRESS"
    echo "CA certificate: $RUN_DIR/ca-lab.crt"
    exit 0
  fi
  sleep 0.1
done

echo "lan gateway did not become ready; see $RUN_DIR/haproxy.log and $SISTERD_LOG_FILE" >&2
exit 1
