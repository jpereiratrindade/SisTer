#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = subprocess.run([
        sys.executable, str(ROOT / "scripts/participation_assess.py"),
        str(ROOT / "contracts/participation/1.0.0/examples/reference-proposed.json"),
        "--commit", "431e6d5f6d20a863ae478a8f1e0a394fd1535d47c", "--json"
    ], cwd=ROOT, capture_output=True, text=True, check=True)
    assessment = json.loads(result.stdout)
    assert assessment["result"] == "PASS"
    assert assessment["gate_effect"] == "none"
    assert "não autoriza" in assessment["limitations"][0]
    print("participation assessment tests ok")


if __name__ == "__main__":
    main()
