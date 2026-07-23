#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-head}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_PATH="$(dirname "$ROOT_DIR")/SisTer-test"
TARGET_PATH="${2:-$DEFAULT_PATH}"

cd "$ROOT_DIR"
source scripts/lib/worktree.sh

MAIN_WORKTREE="$(sister_main_worktree)"
if [[ "$(cd "$ROOT_DIR" && pwd -P)" != "$(cd "$MAIN_WORKTREE" && pwd -P)" ]]; then
  echo "Prepare the test worktree from the main development worktree." >&2
  exit 1
fi

case "$MODE" in
  head)
    if [[ -n "$(git status --porcelain)" ]]; then
      echo "The development worktree has uncommitted changes." >&2
      echo "Commit them before testing HEAD, so the tested revision is reproducible." >&2
      exit 1
    fi
    REF_NAME="HEAD"
    ;;
  release)
    if git remote get-url origin >/dev/null 2>&1; then
      echo "Fetching release tags from origin..."
      git fetch --tags origin
    fi
    REF_NAME="$(git tag --list 'v[0-9]*' --sort=-version:refname | head -n 1)"
    if [[ -z "$REF_NAME" ]]; then
      echo "No release tag matching v<version> was found." >&2
      exit 1
    fi
    ;;
  *)
    echo "Unknown test source: ${MODE}" >&2
    echo "Expected: head or release" >&2
    exit 1
    ;;
esac

REF="$(git rev-parse "${REF_NAME}^{commit}")"

TARGET_PARENT="$(dirname "$TARGET_PATH")"
TARGET_NAME="$(basename "$TARGET_PATH")"
mkdir -p "$TARGET_PARENT"
TARGET_PATH="$(cd "$TARGET_PARENT" && pwd -P)/$TARGET_NAME"

if [[ -e "$TARGET_PATH" ]]; then
  if ! git worktree list --porcelain | grep -Fxq "worktree ${TARGET_PATH}"; then
    echo "Path exists but is not a worktree of this repository: ${TARGET_PATH}" >&2
    exit 1
  fi

  DIRTY="$(
    git -C "$TARGET_PATH" status --porcelain --untracked-files=all \
      | awk '$0 !~ /^\?\? \.run\// { print }'
  )"
  if [[ -n "$DIRTY" ]]; then
    echo "The test worktree has changes that would make synchronization unsafe:" >&2
    echo "$DIRTY" >&2
    exit 1
  fi

  git -C "$TARGET_PATH" switch --detach "$REF"
else
  git worktree add --detach "$TARGET_PATH" "$REF"
fi

TESTED_SHA="$(git -C "$TARGET_PATH" rev-parse HEAD)"
echo "Test worktree ready."
echo "  source: ${MODE}"
echo "  ref:    ${REF_NAME}"
echo "  commit: ${TESTED_SHA}"
echo "  path:   ${TARGET_PATH}"
