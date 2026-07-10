#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
PORT="${2:-8000}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/db/up.sh "$ENV_NAME"
./scripts/db/migrate.sh "$ENV_NAME"
./scripts/db/check.sh "$ENV_NAME"
./scripts/run_quality.sh
./scripts/app/serve.sh "$ENV_NAME" "$PORT"
./scripts/app/smoke.sh "$PORT"

echo "All checks passed for ${ENV_NAME}."
