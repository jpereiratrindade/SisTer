#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/participation/1.0.0/examples/reference-proposed.json"


def main():
    with tempfile.TemporaryDirectory(prefix="sister-participation-") as temporary:
        env = {**os.environ, "SISTER_PARTICIPATION_STORE": str(Path(temporary) / "store")}
        command = [sys.executable, str(ROOT / "scripts/participation_store.py")]
        registered = subprocess.run(command + ["register", str(CONTRACT)], env=env, cwd=ROOT, text=True, capture_output=True)
        assert registered.returncode == 0, registered.stderr
        duplicate = subprocess.run(command + ["register", str(CONTRACT)], env=env, cwd=ROOT, text=True, capture_output=True)
        assert duplicate.returncode == 1, duplicate.stdout + duplicate.stderr
        shown = subprocess.run(command + ["show", "part-reference-mvp01"], env=env, cwd=ROOT, text=True, capture_output=True)
        assert shown.returncode == 0, shown.stderr
        value = json.loads(shown.stdout)
        assert value["participation_id"] == "part-reference-mvp01"
        assert value["state"] == "proposed"
    print("participation persistence tests ok")


if __name__ == "__main__":
    main()
