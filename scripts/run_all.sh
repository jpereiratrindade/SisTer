#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PROFILE=""
UPDATE_SUBSYSTEMS=0
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || { echo "run_all: --profile requires a value" >&2; exit 3; }
      PROFILE="$2"
      shift 2
      ;;
    --update-subsystems)
      UPDATE_SUBSYSTEMS=1
      shift
      ;;
    --help)
      cat <<'USAGE'
Usage:
  ./scripts/run_all.sh [dev|test] [port]
  ./scripts/run_all.sh --profile dev-core|dev-reference|dev-lan|test-core|sec-03v [port]
                       [--update-subsystems]
USAGE
      exit 0
      ;;
    --*)
      echo "run_all: unknown option: $1" >&2
      exit 3
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$PROFILE" ]]; then
  LEGACY_ENV="${POSITIONAL[0]:-dev}"
  case "$LEGACY_ENV" in
    dev) PROFILE="dev-reference" ;;
    test) PROFILE="test-core" ;;
    *) echo "run_all: expected dev or test, got $LEGACY_ENV" >&2; exit 3 ;;
  esac
  LEGACY_PORT="${POSITIONAL[1]:-}"
  [[ ${#POSITIONAL[@]} -le 2 ]] || { echo "run_all: too many arguments" >&2; exit 3; }
else
  LEGACY_PORT="${POSITIONAL[0]:-}"
  [[ ${#POSITIONAL[@]} -le 1 ]] || { echo "run_all: too many arguments" >&2; exit 3; }
fi

PROFILE_OUTPUT="$(python3 scripts/resolve_run_profile.py --profile "$PROFILE")" || exit 3
mapfile -t PROFILE_DATA <<<"$PROFILE_OUTPUT"
[[ ${#PROFILE_DATA[@]} -eq 11 ]] || { echo "run_all: invalid resolved profile" >&2; exit 3; }
ENV_NAME="${PROFILE_DATA[0]}"
PROFILE_PORT="${PROFILE_DATA[1]}"
PROFILE_SCOPE="${PROFILE_DATA[2]}"
ACCESS_SCOPE="${PROFILE_DATA[3]}"
CORE_TRANSPORT="${PROFILE_DATA[4]}"
PUBLIC_GATEWAY="${PROFILE_DATA[5]}"
GATEWAY_POLICY="${PROFILE_DATA[6]}"
SUBSYSTEM_SELECTION="${PROFILE_DATA[7]}"
SUBSYSTEM_PROJECTS="${PROFILE_DATA[8]}"
SUBSYSTEM_REQUIRED="${PROFILE_DATA[9]}"
SUBSYSTEM_FAILURE_POLICY="${PROFILE_DATA[10]}"
[[ "$SUBSYSTEM_PROJECTS" == "-" ]] && SUBSYSTEM_PROJECTS=""
[[ "$SUBSYSTEM_REQUIRED" == "-" ]] && SUBSYSTEM_REQUIRED=""
PORT="${LEGACY_PORT:-$PROFILE_PORT}"

REFERENCE_SELECTED=0
if [[ ",$SUBSYSTEM_PROJECTS," == *,sister_reference,* ]]; then
  REFERENCE_SELECTED=1
  export SISTER_ENABLE_REFERENCE_SUBSYSTEM=true
  export SISTER_REFERENCE_PORT=19001
  SISTER_INTERNAL_PROXY_TOKEN="$(openssl rand -hex 32)"
  export SISTER_INTERNAL_PROXY_TOKEN
else
  export SISTER_ENABLE_REFERENCE_SUBSYSTEM=false
fi

if [[ $UPDATE_SUBSYSTEMS -eq 1 && "$SUBSYSTEM_SELECTION" == "none" ]]; then
  echo "run_all: --update-subsystems requires a profile that selects subsystems" >&2
  exit 3
fi

if [[ "$GATEWAY_POLICY" == "required" ]]; then
  if [[ -z "${GATEWAY_HAPROXY_BIN:-}" || "${GATEWAY_HAPROXY_BIN:0:1}" != "/" || ! -x "$GATEWAY_HAPROXY_BIN" ]]; then
    echo "SEC-03V prerequisite BLOCKED: configure an absolute executable GATEWAY_HAPROXY_BIN" >&2
    exit 2
  fi
  if [[ "$PUBLIC_GATEWAY" == "lan-required" && -z "${GATEWAY_LAN_ADDRESS:-}" ]]; then
    echo "dev-lan prerequisite BLOCKED: configure GATEWAY_LAN_ADDRESS with the private LAN IPv4" >&2
    exit 2
  fi
  if [[ "$PUBLIC_GATEWAY" == "lan-required" ]] && ss -lnt | grep -E -q ':(8443)\b'; then
    echo "dev-lan prerequisite BLOCKED: port 8443 is already occupied" >&2
    exit 2
  fi
fi

echo "SisTer run profile: $PROFILE ($PROFILE_SCOPE)"
if [[ "$PROFILE_SCOPE" == "sec-03v-prerequisites" ]]; then
  echo "This profile validates prerequisites only; it cannot close SEC-03V."
fi

source scripts/lib/sister_env.sh
source scripts/lib/worktree.sh
sister_load_env "$ENV_NAME"
sister_assert_environment_worktree "$ENV_NAME" "$ROOT_DIR"

# A suíte de isolamento deve observar somente os processos que ela própria cria.
./scripts/app/stop.sh "$ENV_NAME" >/dev/null
./scripts/app/stop_unmanaged_sister_containers.sh "$COMPOSE_PROJECT_NAME"
python3 scripts/app/execution_lifecycle.py begin \
  --profile "$PROFILE" --environment "$ENV_NAME" --access-scope "$ACCESS_SCOPE" >/dev/null
cleanup_failed_execution() {
  local status="$?"
  if [[ $status -ne 0 ]]; then
    python3 scripts/app/execution_lifecycle.py stop --environment "$ENV_NAME" >/dev/null 2>&1 || true
  fi
  return "$status"
}
trap cleanup_failed_execution EXIT

./scripts/db/up.sh "$ENV_NAME"
./scripts/db/migrate.sh "$ENV_NAME"
./scripts/db/check.sh "$ENV_NAME"
./scripts/run_quality.sh
./scripts/app/stop_unmanaged_sister_containers.sh "$COMPOSE_PROJECT_NAME"
if [[ "$CORE_TRANSPORT" == "loopback-tcp" ]]; then
  ./scripts/app/serve.sh "$ENV_NAME" "$PORT" --no-build
  ./scripts/app/smoke.sh "$PORT"
fi

SUBSYSTEM_REPORT="$ROOT_DIR/.run/maturity/subsystems.json"
rm -f "$SUBSYSTEM_REPORT"
SUBSYSTEM_CODE=0
if [[ "$SUBSYSTEM_SELECTION" != "none" ]]; then
  SUBSYSTEM_ARGS=(--report "$SUBSYSTEM_REPORT")
  if [[ "$SUBSYSTEM_SELECTION" == "listed" ]]; then
    IFS=',' read -r -a PROJECTS <<<"$SUBSYSTEM_PROJECTS"
    for project in "${PROJECTS[@]}"; do
      SUBSYSTEM_ARGS+=(--project "$project")
    done
  fi
  if [[ -n "$SUBSYSTEM_REQUIRED" ]]; then
    IFS=',' read -r -a REQUIRED_PROJECTS <<<"$SUBSYSTEM_REQUIRED"
    for project in "${REQUIRED_PROJECTS[@]}"; do
      SUBSYSTEM_ARGS+=(--require "$project")
    done
  fi
  if [[ "$SUBSYSTEM_FAILURE_POLICY" == "block" ]]; then
    SUBSYSTEM_ARGS+=(--strict)
  fi
  if [[ $UPDATE_SUBSYSTEMS -eq 1 ]]; then
    SUBSYSTEM_ARGS+=(--refresh-changed)
  fi
  set +e
  ./scripts/subsystems/ensure.sh "$ENV_NAME" "${SUBSYSTEM_ARGS[@]}"
  SUBSYSTEM_CODE=$?
  set -e
  if [[ $SUBSYSTEM_CODE -eq 3 ]]; then
    echo "Environment status: ORCHESTRATOR_ERROR" >&2
    exit 3
  fi
fi

GATEWAY_STATUS="NOT_REQUESTED"
PUBLIC_URL=""
if [[ "$PUBLIC_GATEWAY" == "lan-required" && $SUBSYSTEM_CODE -eq 0 ]]; then
  set +e
  ./scripts/run_gateway_lan_lab.sh --environment "$ENV_NAME" --no-prepare
  GATEWAY_CODE=$?
  set -e
  if [[ $GATEWAY_CODE -eq 0 ]]; then
    GATEWAY_STATUS="READY"
    PUBLIC_URL="https://${GATEWAY_ALLOWED_HOST:-sister-gateway.test}:8443"
  else
    GATEWAY_STATUS="FAIL"
  fi
elif [[ "$PUBLIC_GATEWAY" == "validation-only" && $SUBSYSTEM_CODE -eq 0 ]]; then
  GATEWAY_STATUS="VALIDATED"
fi

LIFECYCLE_ARGS=(finalize --environment "$ENV_NAME")
FINALIZE_ARGS=(--profile "$PROFILE" --access-scope "$ACCESS_SCOPE" --core-transport "$CORE_TRANSPORT" --gateway-status "$GATEWAY_STATUS")
[[ -n "$PUBLIC_URL" ]] && FINALIZE_ARGS+=(--public-url "$PUBLIC_URL")
if [[ -f "$SUBSYSTEM_REPORT" ]]; then
  LIFECYCLE_ARGS+=(--subsystems-report "$SUBSYSTEM_REPORT")
  FINALIZE_ARGS+=(--subsystems-report "$SUBSYSTEM_REPORT")
fi
python3 scripts/app/execution_lifecycle.py "${LIFECYCLE_ARGS[@]}" || exit 3
python3 scripts/quality/finalize_run.py "${FINALIZE_ARGS[@]}" || exit 3

if [[ $SUBSYSTEM_CODE -eq 2 || "$GATEWAY_STATUS" == "FAIL" ]]; then
  exit 2
fi
trap - EXIT
