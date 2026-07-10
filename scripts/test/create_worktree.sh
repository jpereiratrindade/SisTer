#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_PATH="$(dirname "$ROOT_DIR")/SisTer-test"
TARGET_PATH="${1:-$DEFAULT_PATH}"

if [[ -e "$TARGET_PATH" ]]; then
  echo "Test worktree path already exists: $TARGET_PATH" >&2
  exit 1
fi

if [[ -n "$(git -C "$ROOT_DIR" status --porcelain)" ]]; then
  echo "The main worktree has uncommitted changes." >&2
  echo "Commit or stash them before creating SisTer-test, so the test worktree starts from a reproducible state." >&2
  exit 1
fi

git -C "$ROOT_DIR" worktree add --detach "$TARGET_PATH" HEAD

cat <<MSG
Created test worktree:
  $TARGET_PATH

Next:
  cd "$TARGET_PATH"
  ./scripts/db/up.sh test
  ./scripts/db/migrate.sh test
  ./scripts/run_quality.sh
MSG
