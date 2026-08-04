#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/releases/v0.2.10.yaml"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def revision(commit):
    return f"R{int(git('rev-list', '--count', '--first-parent', commit)):06d}"


def main():
    import yaml
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    baseline = manifest["engineering_release"]["commit"]
    current = git("rev-parse", "HEAD")
    tag_commit = git("rev-list", "-n", "1", manifest["engineering_release"]["tag"])
    try:
        git("merge-base", "--is-ancestor", baseline, current)
        descendant = True
    except subprocess.CalledProcessError:
        descendant = False
    if tag_commit != baseline or not descendant:
        relationship = "DIVERGED"
    elif current == baseline:
        relationship = "RELEASE_ALIGNED"
    else:
        relationship = "POST_RELEASE_DEVELOPMENT"
    state = {"RELEASE_ALIGNED": "RELEASED", "POST_RELEASE_DEVELOPMENT": "DEVELOPMENT", "DIVERGED": "DIVERGED"}[relationship]
    output = {
        "current_revision": revision(current),
        "current_commit": current,
        "state": state,
        "published_release": manifest["engineering_release"]["tag"],
        "release_revision": revision(baseline),
        "baseline_commit": baseline,
        "observed_commit": current,
        "baseline_relationship": relationship,
        "commits_after_release": int(git("rev-list", "--count", "--first-parent", f"{baseline}..{current}")),
        "raf_revision": revision("db0edb5"),
        "publication_authorized": False if relationship != "RELEASE_ALIGNED" else manifest["publication"]["published"]
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if relationship == "DIVERGED" else 0


if __name__ == "__main__":
    sys.exit(main())
