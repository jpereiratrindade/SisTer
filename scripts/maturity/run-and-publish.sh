#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ "${SGE_INTERNAL_PUBLISH:-}" != "1" ]]; then
  printf 'Este é um detalhe interno do SGE. Use a interface única:\n' >&2
  printf '  ./scripts/sge maturity publish [estágio] [opções]\n' >&2
  exit 2
fi

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

STAGE=""
COMPONENT="sister-core"
COMPONENT_ROOT="$REPO"
ENGINE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --component) COMPONENT="$2"; shift 2 ;;
    --component-root) COMPONENT_ROOT="$2"; shift 2 ;;
    --engine) ENGINE="$2"; shift 2 ;;
    -*) die "Opção desconhecida: $1" ;;
    *) STAGE="$1"; shift ;;
  esac
done

if [[ -z "$STAGE" ]]; then
  if ! STAGE="$(infer_stage)"; then
    printf 'Uso: %s [pre-alpha|alpha|beta|gamma|production] [--engine legacy|declarative|compare]\n' "$0" >&2
    printf 'Não foi possível inferir o estágio a partir de .sister/status.yml\n' >&2
    exit 2
  fi
  printf 'Estágio inferido: %s\n' "$STAGE"
fi

case "$STAGE" in
  pre-alpha|alpha|beta|gamma|production) ;;
  *) printf 'Uso: %s [pre-alpha|alpha|beta|gamma|production] [--engine legacy|declarative|compare]\n' "$0" >&2; exit 2;;
esac

RUNTIME_ROOT="$REPO/.run/maturity"
COMPONENTS_DIR="$RUNTIME_ROOT/components"
COMP_DIR="$COMPONENTS_DIR/$COMPONENT"
HISTORY_ROOT="$COMP_DIR/history"
REPORT_ROOT="$REPO/build/maturity"
mkdir -p "$RUNTIME_ROOT" "$COMP_DIR" "$HISTORY_ROOT" "$REPORT_ROOT"

CANDIDATE="$(mktemp "$RUNTIME_ROOT/.candidate.XXXXXX.json")"
trap 'rm -f "$CANDIDATE"' EXIT

set +e
ENGINE_ARGS=()
if [[ -n "$ENGINE" ]]; then
  ENGINE_ARGS=(--engine "$ENGINE")
fi
python3 "$REPO/scripts/maturity/evaluate-engine.py" \
  --repo "$REPO" \
  --component-root "$COMPONENT_ROOT" \
  --component "$COMPONENT" \
  --profile "engineering/maturity/profiles/$COMPONENT.yaml" \
  --stage "$STAGE" \
  --status-json "$CANDIDATE" \
  "${ENGINE_ARGS[@]}"
GATE_STATUS=$?
set -e

if [[ ! -s "$CANDIDATE" ]]; then
  printf 'O gate não produziu uma atestação JSON válida; latest.json não foi alterado.\n' >&2
  exit "$GATE_STATUS"
fi

# The python validator might need some updates for the promotion block, we assume it's schema aware.
# Actually wait, validate-status.py validates the JSON schema. We updated the schema so it should pass.
python3 "$REPO/scripts/maturity/validate-status.py" "$CANDIDATE"
mv "$CANDIDATE" "$COMP_DIR/latest.json"

python3 "$REPO/scripts/maturity/update-history.py" \
  "$COMP_DIR/latest.json" "$HISTORY_ROOT"

# Atualizar o agregador de componentes do ecossistema
python3 "$REPO/scripts/maturity/aggregate-components.py"
python3 "$REPO/scripts/maturity/build-catalog.py"

INDEX_FILE="$RUNTIME_ROOT/components.json"

# Copy the latest component evaluation to the root so the UI can still consume it
cp "$COMP_DIR/latest.json" "$RUNTIME_ROOT/latest.json"

printf 'Status publicado para %s: %s\n' "$COMPONENT" "$COMP_DIR/latest.json"
printf 'Engine executado: %s\n' "$ENGINE"
printf 'Histórico atualizado para %s: %s\n' "$COMPONENT" "$HISTORY_ROOT/index.json"
printf 'Índice de componentes atualizado: %s\n' "$INDEX_FILE"
printf 'Status global atualizado: %s\n' "$RUNTIME_ROOT/latest.json"
exit "$GATE_STATUS"
