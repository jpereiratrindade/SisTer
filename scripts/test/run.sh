#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-head}"
PORT="${2:-8001}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_PATH="${3:-$(dirname "$ROOT_DIR")/SisTer-test}"

if [[ "$TEST_PATH" != /* ]]; then
  TEST_PATH="$ROOT_DIR/$TEST_PATH"
fi

"$ROOT_DIR/scripts/test/prepare_worktree.sh" "$MODE" "$TEST_PATH"

if [[ ! -x "$TEST_PATH/scripts/run_all.sh" ]]; then
  echo "The selected revision does not contain scripts/run_all.sh." >&2
  echo "Publish a newer release containing the environment workflow before using release mode." >&2
  exit 1
fi

cd "$TEST_PATH"
exec ./scripts/run_all.sh test "$PORT"
