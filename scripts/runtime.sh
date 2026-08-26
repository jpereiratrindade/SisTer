#!/usr/bin/env bash
# SISTER-INFRA-INSTALLED-RUNTIME
#
# Runtime de release instalada do SisTer.
# Não compila, não executa CTest e não qualifica código.
set -Eeuo pipefail
IFS=$'\n\t'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT_DIR"

ENV_NAME="${SISTER_RUNTIME_ENV:-dev}"
COMPONENT_CONFIG="${SISTER_COMPONENT_CONFIG_FILE:-$ROOT_DIR/.env}"

if [[ -f "$COMPONENT_CONFIG" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$COMPONENT_CONFIG"
  set +a
fi

# shellcheck disable=SC1091
source scripts/lib/sister_env.sh
sister_load_env "$ENV_NAME"

load_deployment_binding() {
  local resolved="${SISTER_RESOLVED_DEPLOYMENT_FILE:-}"
  [[ -n "$resolved" ]] || return 0
  [[ -f "$resolved" ]] || {
    echo "[FAIL] deployment resolvido ausente: $resolved" >&2
    return 1
  }
  command -v jq >/dev/null 2>&1 || {
    echo "[FAIL] jq é necessário para consumir deployment resolvido" >&2
    return 1
  }

  local system_id transport listen port
  system_id="$(jq -er '.system_id' "$ROOT_DIR/.sister/component.json")"
  transport="$(jq -er --arg id "$system_id" \
    '.components[] | select(.system_id == $id) | .runtime.transport' \
    "$resolved")"
  [[ "$transport" == "tcp" ]] || {
    echo "[FAIL] runtime SisTer ainda requer binding TCP" >&2
    return 1
  }
  listen="$(jq -er --arg id "$system_id" \
    '.components[] | select(.system_id == $id) | .runtime.listen' \
    "$resolved")"
  port="$(jq -er --arg id "$system_id" \
    '.components[] | select(.system_id == $id) | .runtime.port' \
    "$resolved")"
  [[ "$listen" == "127.0.0.1" ]] || {
    echo "[FAIL] runtime SisTer exige TCP loopback; atual=$listen" >&2
    return 1
  }
  export SISTER_RUNTIME_PORT="$port"
}

load_deployment_binding

PORT="${SISTER_RUNTIME_PORT:-$SISTER_APP_PORT}"
BIN="$ROOT_DIR/build/apps/sisterd/sisterd"

health_ok() {
  curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1
}

start_runtime() {
  [[ -x "$BIN" ]] || {
    echo "[FAIL] artefato qualificado ausente: $BIN" >&2
    exit 2
  }

  if health_ok; then
    echo "[PASS] SisTer runtime já está saudável em 127.0.0.1:${PORT}"
    return 0
  fi

  echo "[runtime] Garantindo banco SisTer..."
  ./scripts/db/up.sh "$ENV_NAME"
  ./scripts/db/migrate.sh "$ENV_NAME"
  ./scripts/db/check.sh "$ENV_NAME"

  echo "[runtime] Iniciando sisterd qualificado sem rebuild..."
  ./scripts/app/serve.sh "$ENV_NAME" "$PORT" --no-build
  ./scripts/app/smoke.sh "$PORT"

  health_ok || {
    echo "[FAIL] SisTer runtime não ficou saudável" >&2
    exit 3
  }

  echo "[PASS] SisTer installed runtime saudável em 127.0.0.1:${PORT}"
}

stop_runtime() {
  ./scripts/app/stop.sh "$ENV_NAME" >/dev/null 2>&1 || true
  echo "[PASS] SisTer installed runtime parado; dados persistentes preservados"
}

status_runtime() {
  if health_ok; then
    echo "[UP] SisTer installed runtime 127.0.0.1:${PORT}"
  else
    echo "[DOWN] SisTer installed runtime"
    exit 1
  fi
}

health_runtime() {
  curl --fail --silent --show-error \
    "http://127.0.0.1:${PORT}/api/health"
  printf '\n'
}

case "${1:-status}" in
  start) start_runtime ;;
  stop) stop_runtime ;;
  restart)
    stop_runtime
    start_runtime
    ;;
  status) status_runtime ;;
  health) health_runtime ;;
  *)
    echo "usage: $0 start|stop|restart|status|health" >&2
    exit 64
    ;;
esac
