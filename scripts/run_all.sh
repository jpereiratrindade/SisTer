#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source scripts/lib/sister_env.sh
source scripts/lib/worktree.sh
sister_load_env "$ENV_NAME"
sister_assert_environment_worktree "$ENV_NAME" "$ROOT_DIR"
PORT="${2:-$SISTER_APP_PORT}"

./scripts/db/up.sh "$ENV_NAME"
./scripts/db/migrate.sh "$ENV_NAME"
./scripts/db/check.sh "$ENV_NAME"
./scripts/run_quality.sh
./scripts/app/serve.sh "$ENV_NAME" "$PORT"
./scripts/app/smoke.sh "$PORT"

echo "All checks passed for ${ENV_NAME}."
