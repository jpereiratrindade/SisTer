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
ACTION="${1:-status}"

if [[ -f "$COMPONENT_CONFIG" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$COMPONENT_CONFIG"
  set +a
fi

RUNTIME_MODE="${SISTER_RUNTIME_MODE:-installed}"
RUNTIME_RUN_DIR="${SISTER_RUNTIME_RUN_DIR:-$ROOT_DIR/.run}"
PREVIEW_DB_PORT_FILE=""

configure_preview_identity() {
  [[ "$RUNTIME_MODE" == "dev-preview" ]] || return 0

  local required value state_dir data_dir
  for required in \
    SISTER_RUNTIME_INSTANCE_ID \
    SISTER_RUNTIME_STATE_DIR \
    SISTER_RUNTIME_RUN_DIR \
    SISTER_RUNTIME_DATA_DIR; do
    value="${!required:-}"
    [[ -n "$value" ]] || {
      echo "[FAIL] DEV Preview requer $required" >&2
      return 1
    }
  done
  [[ "${SISTER_RUNTIME_CLEANUP_SCOPE:-}" == "preview-only" ]] || {
    echo "[FAIL] DEV Preview requer SISTER_RUNTIME_CLEANUP_SCOPE=preview-only" >&2
    return 1
  }
  [[ "$SISTER_RUNTIME_INSTANCE_ID" =~ ^[a-zA-Z0-9._-]+$ ]] || {
    echo "[FAIL] identidade de DEV Preview inválida" >&2
    return 1
  }
  for required in \
    SISTER_RUNTIME_STATE_DIR \
    SISTER_RUNTIME_RUN_DIR \
    SISTER_RUNTIME_DATA_DIR; do
    value="${!required}"
    [[ "$value" == /* ]] || {
      echo "[FAIL] $required deve ser absoluto em DEV Preview" >&2
      return 1
    }
  done

  state_dir="$(realpath -m -- "$SISTER_RUNTIME_STATE_DIR")"
  data_dir="$(realpath -m -- "$SISTER_RUNTIME_DATA_DIR")"
  [[ "$data_dir" == "$state_dir"/* ]] || {
    echo "[FAIL] SISTER_RUNTIME_DATA_DIR deve pertencer ao state dir do Preview" >&2
    return 1
  }

  RUNTIME_RUN_DIR="$(realpath -m -- "$SISTER_RUNTIME_RUN_DIR")"
  mkdir -p -- "$RUNTIME_RUN_DIR" "$state_dir" "$data_dir"
  PREVIEW_DB_PORT_FILE="$RUNTIME_RUN_DIR/postgresql.port"

  if [[ "$ACTION" == "start" || "$ACTION" == "restart" ]]; then
    python3 - "$PREVIEW_DB_PORT_FILE" <<'PY'
import socket
import sys
from pathlib import Path

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
Path(sys.argv[1]).write_text(f"{port}\n", encoding="utf-8")
PY
  elif [[ ! -s "$PREVIEW_DB_PORT_FILE" ]]; then
    printf '%s\n' "1" >"$PREVIEW_DB_PORT_FILE"
  fi

  SISTER_PREVIEW_DB_PORT="$(<"$PREVIEW_DB_PORT_FILE")"
  [[ "$SISTER_PREVIEW_DB_PORT" =~ ^[0-9]+$ ]] || {
    echo "[FAIL] porta PostgreSQL inválida no estado do Preview" >&2
    return 1
  }
  export SISTER_PREVIEW_DB_PORT
}

configure_preview_identity

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

derive_ecosystem_projection() {
  local resolved="${SISTER_RESOLVED_DEPLOYMENT_FILE:-}"
  [[ -n "$resolved" && -f "$resolved" ]] || return 0
  command -v jq >/dev/null 2>&1 || return 0

  mkdir -p "$RUNTIME_RUN_DIR"
  local projection_file="$RUNTIME_RUN_DIR/ecosystem_projection.tsv"
  "$ROOT_DIR/scripts/app/render-ecosystem-projection.sh" \
    "$resolved" "$projection_file"
  export SISTER_ECOSYSTEM_PROJECTION_FILE="$projection_file"
}

load_deployment_binding
derive_ecosystem_projection

PORT="${SISTER_RUNTIME_PORT:-$SISTER_APP_PORT}"
BIN="$ROOT_DIR/build/apps/sisterd/sisterd"
PID_FILE="$RUNTIME_RUN_DIR/sisterd-${ENV_NAME}.pid"
IDENTITY_TOOL="$ROOT_DIR/scripts/app/process_identity.py"

health_ok() {
  curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1
}

runtime_owned() {
  python3 "$IDENTITY_TOOL" validate \
    --pid-file "$PID_FILE" \
    --environment "$ENV_NAME" \
    --executable "$BIN" >/dev/null 2>&1
}

start_runtime() {
  [[ -x "$BIN" ]] || {
    echo "[FAIL] artefato qualificado ausente: $BIN" >&2
    exit 2
  }

  if health_ok; then
    if runtime_owned; then
      echo "[PASS] SisTer runtime desta release já está saudável em 127.0.0.1:${PORT}"
      return 0
    fi
    echo "[FAIL] binding 127.0.0.1:${PORT} está ocupado por runtime que não pertence a esta release" >&2
    exit 4
  fi

  echo "[runtime] Garantindo banco SisTer..."
  ./scripts/db/up.sh "$ENV_NAME"
  ./scripts/db/migrate.sh "$ENV_NAME"
  ./scripts/db/check.sh "$ENV_NAME"

  echo "[runtime] Iniciando sisterd qualificado sem rebuild..."
  ./scripts/app/serve.sh "$ENV_NAME" "$PORT" --no-build
  if ! ./scripts/app/smoke.sh "$PORT"; then
    echo "[FAIL] smoke pós-start falhou; compensando runtime recém-iniciado" >&2
    ./scripts/app/stop.sh "$ENV_NAME" --core-only >/dev/null 2>&1 || true
    exit 3
  fi

  health_ok || {
    echo "[FAIL] SisTer runtime não ficou saudável" >&2
    exit 3
  }

  echo "[PASS] SisTer installed runtime saudável em 127.0.0.1:${PORT}"
}

stop_runtime() {
  if [[ "$RUNTIME_MODE" == "dev-preview" ]]; then
    ./scripts/app/stop.sh "$ENV_NAME" --core-only >/dev/null 2>&1 || true
    ./scripts/db/destroy.sh "$ENV_NAME" >/dev/null 2>&1 || true
    if command -v podman >/dev/null 2>&1 && [[ -d "$SISTER_RUNTIME_DATA_DIR" ]]; then
      podman unshare chown -R 0:0 -- "$SISTER_RUNTIME_DATA_DIR" >/dev/null 2>&1 || true
      chmod -R u+rwX -- "$SISTER_RUNTIME_DATA_DIR" >/dev/null 2>&1 || true
    fi
    rm -f -- "$PREVIEW_DB_PORT_FILE"
  else
    ./scripts/app/stop.sh "$ENV_NAME" >/dev/null 2>&1 || true
  fi
  echo "[PASS] SisTer installed runtime parado; dados persistentes preservados"
}

status_runtime() {
  if runtime_owned && health_ok; then
    echo "[UP] SisTer installed runtime 127.0.0.1:${PORT}"
  elif health_ok; then
    echo "[DRIFT] 127.0.0.1:${PORT} responde, mas o runtime não pertence a esta release" >&2
    exit 1
  else
    echo "[DOWN] SisTer installed runtime"
    exit 1
  fi
}

health_runtime() {
  runtime_owned || {
    echo "[FAIL] runtime ativo não pertence a esta release" >&2
    exit 1
  }
  curl --fail --silent --show-error \
    "http://127.0.0.1:${PORT}/api/health"
  printf '\n'
}

case "$ACTION" in
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
