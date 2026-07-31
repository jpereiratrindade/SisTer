#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

STAGE="${1:-}"
case "$STAGE" in
  pre-alpha|alpha|beta|gamma|production) ;;
  *) printf 'Uso: %s <pre-alpha|alpha|beta|gamma|production>\n' "$0" >&2; exit 2;;
esac

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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
