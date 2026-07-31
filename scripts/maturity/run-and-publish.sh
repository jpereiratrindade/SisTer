#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

infer_stage() {
  local status_file="$REPO/.sister/status.yml"
  [[ -f "$status_file" ]] || return 1
  local raw_stage
  raw_stage="$(sed -n 's/^[[:space:]]*stage[[:space:]]*:[[:space:]]*//p' "$status_file" | head -n 1 | tr -d '\"'\''[:space:]')"
  case "$raw_stage" in
    development_prototype|development_provisional|pre-alpha) printf 'pre-alpha\n' ;;
    alpha|beta|gamma|production) printf '%s\n' "$raw_stage" ;;
    *) return 1 ;;
  esac
}

STAGE="${1:-}"
if [[ -z "$STAGE" ]]; then
  if ! STAGE="$(infer_stage)"; then
    printf 'Uso: %s [pre-alpha|alpha|beta|gamma|production]\n' "$0" >&2
    printf 'Não foi possível inferir o estágio a partir de .sister/status.yml\n' >&2
    exit 2
  fi
  printf 'Estágio inferido: %s\n' "$STAGE"
fi

case "$STAGE" in
  pre-alpha|alpha|beta|gamma|production) ;;
  *) printf 'Uso: %s [pre-alpha|alpha|beta|gamma|production]\n' "$0" >&2; exit 2;;
esac

RUNTIME_ROOT="$REPO/.run/maturity"
HISTORY_ROOT="$RUNTIME_ROOT/history"
REPORT_ROOT="$REPO/build/maturity"
mkdir -p "$RUNTIME_ROOT" "$HISTORY_ROOT" "$REPORT_ROOT"

CANDIDATE="$(mktemp "$RUNTIME_ROOT/.candidate.XXXXXX.json")"
trap 'rm -f "$CANDIDATE"' EXIT

set +e
"$REPO/scripts/verify-sister-maturity.sh" \
  --stage "$STAGE" \
  --report "$REPORT_ROOT/$STAGE-report.md" \
  --status-json "$CANDIDATE" \
  --repo "$REPO"
GATE_STATUS=$?
set -e

python3 "$REPO/scripts/maturity/validate-status.py" "$CANDIDATE"
mv "$CANDIDATE" "$RUNTIME_ROOT/latest.json"
python3 "$REPO/scripts/maturity/update-history.py" \
  "$RUNTIME_ROOT/latest.json" "$HISTORY_ROOT"

printf 'Status publicado: %s\n' "$RUNTIME_ROOT/latest.json"
printf 'Histórico atualizado: %s\n' "$HISTORY_ROOT/index.json"
exit "$GATE_STATUS"
