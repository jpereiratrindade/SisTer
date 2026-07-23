#!/usr/bin/env bash

sister_main_worktree() {
  git worktree list --porcelain | sed -n 's/^worktree //p' | head -n 1
}

sister_assert_environment_worktree() {
  local env_name="$1"
  local root_dir="$2"
  local main_worktree

  root_dir="$(cd "$root_dir" && pwd -P)"
  main_worktree="$(sister_main_worktree)"
  main_worktree="$(cd "$main_worktree" && pwd -P)"

  case "$env_name" in
    dev)
      if [[ "$root_dir" != "$main_worktree" ]]; then
        echo "The dev flow must run in the main worktree: ${main_worktree}" >&2
        return 1
      fi
      ;;
    test)
      if [[ "$root_dir" == "$main_worktree" ]]; then
        echo "The test flow must run in a separate Git worktree." >&2
        echo "From the main worktree, use: ./scripts/test/run.sh head" >&2
        return 1
      fi
      ;;
  esac
}
