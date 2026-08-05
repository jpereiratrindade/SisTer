#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="test"
PREPARE=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment)
      [[ $# -ge 2 ]] || { echo "--environment requires a value" >&2; exit 3; }
      ENV_NAME="$2"
      shift 2
      ;;
    --no-prepare)
      PREPARE=0
      shift
      ;;
    *) echo "unknown option: $1" >&2; exit 3 ;;
  esac
done
[[ "$ENV_NAME" =~ ^(dev|test)$ ]] || { echo "invalid environment: $ENV_NAME" >&2; exit 3; }
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
if [[ -n "${GATEWAY_NEXO_HOST:-}" ]]; then
  export GATEWAY_ADDITIONAL_HOSTS="$GATEWAY_NEXO_HOST"
  export SISTER_NEXO_PUBLIC_URL="${SISTER_NEXO_PUBLIC_URL:-https://${GATEWAY_NEXO_HOST}:8443}"
  export SISTER_NEXO_PORT="${SISTER_NEXO_PORT:-${GATEWAY_NEXO_PORT:-}}"
fi

mkdir -p "$RUN_DIR"
chmod 700 "$RUN_DIR"
cleanup_on_error() {
  local status="$?"
  if [[ "$status" -ne 0 ]]; then
    SISTER_COMPONENT_STOP_ONLY=1 \
      "$ROOT_DIR/scripts/stop_gateway_lan_lab.sh" >/dev/null 2>&1 || true
  fi
  return "$status"
}
trap cleanup_on_error EXIT

if [[ -f "$SISTERD_PID_FILE" || -f "$GATEWAY_PID_FILE" ]]; then
  echo "lan gateway appears to be running; use scripts/stop_gateway_lan_lab.sh first" >&2
  exit 1
fi

source "$ROOT_DIR/scripts/lib/sister_env.sh"
sister_load_env "$ENV_NAME"
if [[ $PREPARE -eq 1 ]]; then
  "$ROOT_DIR/scripts/db/up.sh" "$ENV_NAME"
  "$ROOT_DIR/scripts/db/migrate.sh" "$ENV_NAME"
  cmake -S "$ROOT_DIR" -B "$ROOT_DIR/build"
  cmake --build "$ROOT_DIR/build" --target sisterd --parallel
elif [[ ! -x "$ROOT_DIR/build/apps/sisterd/sisterd" ]]; then
  echo "tested sisterd artifact is missing" >&2
  exit 1
fi
"$ROOT_DIR/scripts/create_gateway_lab_certificate.sh" "$GATEWAY_ALLOWED_HOST"

rm -f "$SISTERD_SOCKET"
launch_prefix=()
if command -v setsid >/dev/null 2>&1; then
  launch_prefix=(setsid)
fi

"${launch_prefix[@]}" env \
  SISTER_ENV="$ENV_NAME" \
  SISTER_LISTENER_MODE=systemd-unix \
  SISTER_ACTIVATED_SOCKET_PATH="$SISTERD_SOCKET" \
  SISTER_WEB_ROOT="$ROOT_DIR/web" \
  SISTER_AUTH_FILE="$RUN_DIR/auth-users.tsv" \
  SISTER_ENABLE_HTTP_BOOTSTRAP=false \
  SISTER_ENABLE_LEGACY_PROXY=false \
  SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY=false \
  SISTER_ENABLE_REFERENCE_SUBSYSTEM="${SISTER_ENABLE_REFERENCE_SUBSYSTEM:-false}" \
  SISTER_REFERENCE_PORT="${SISTER_REFERENCE_PORT:-19001}" \
  SISTER_INTERNAL_PROXY_TOKEN="${SISTER_INTERNAL_PROXY_TOKEN:-}" \
  SISTER_NEXO_PUBLIC_URL="${SISTER_NEXO_PUBLIC_URL:-}" \
  SISTER_NEXO_PORT="${SISTER_NEXO_PORT:-}" \
  SISTER_SUBSYSTEM_HEALTH_TIMEOUT_MS="${SISTER_SUBSYSTEM_HEALTH_TIMEOUT_MS:-800}" \
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

for _ in $(seq 1 120); do
  if ! kill -0 "$gateway_pid" >/dev/null 2>&1; then
    echo "lan gateway failed to start; see $RUN_DIR/haproxy.log" >&2
    exit 1
  fi
  if curl --noproxy '*' --connect-timeout 1 --max-time 2 \
      --silent --show-error --fail \
      --resolve "$GATEWAY_ALLOWED_HOST:8443:$GATEWAY_LAN_ADDRESS" \
      --cacert "$RUN_DIR/ca-lab.crt" \
      "https://$GATEWAY_ALLOWED_HOST:8443/api/health" >/dev/null 2>&1; then
    echo "lan gateway running on https://$GATEWAY_ALLOWED_HOST:8443"
    echo "LAN address: $GATEWAY_LAN_ADDRESS"
    echo "CA certificate: $RUN_DIR/ca-lab.crt"
    echo
    echo "Same laptop: add '$GATEWAY_LAN_ADDRESS $GATEWAY_ALLOWED_HOST' to /etc/hosts."
    echo "Other computer: copy $RUN_DIR/ca-lab.crt and add the same /etc/hosts entry."
    echo "Client check: scripts/check_gateway_lan_access.sh $GATEWAY_LAN_ADDRESS /path/to/ca-lab.crt"
    echo "Browser URL: https://$GATEWAY_ALLOWED_HOST:8443"
    if [[ -n "${GATEWAY_NEXO_HOST:-}" ]]; then
      echo "Nexo URL: https://$GATEWAY_NEXO_HOST:8443"
    fi
    trap - EXIT
    exit 0
  fi
  sleep 0.1
done

echo "lan gateway did not become ready; see $RUN_DIR/haproxy.log and $SISTERD_LOG_FILE" >&2
exit 1
