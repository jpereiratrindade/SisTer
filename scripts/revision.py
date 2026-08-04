#!/usr/bin/env python3
"""Show the current sequential development revision of main."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    count = int(git("rev-list", "--count", "--first-parent", "HEAD"))
    payload = {
        "revision": f"r{count:04d}",
        "commit": git("rev-parse", "--short", "HEAD"),
        "branch": git("branch", "--show-current"),
        "worktree": "clean" if not git("status", "--porcelain") else "dirty",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
