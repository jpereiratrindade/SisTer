#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_PATH="$(dirname "$ROOT_DIR")/SisTer-test"
TARGET_PATH="${1:-$DEFAULT_PATH}"

exec "$ROOT_DIR/scripts/test/prepare_worktree.sh" head "$TARGET_PATH"
