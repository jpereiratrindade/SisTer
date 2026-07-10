#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "mcp" / "contracts"
required_keys = {"name", "allowed_modes", "risk_level", "preconditions", "required_evidence", "forbidden_actions"}

ok = True
for path in sorted(CONTRACT_DIR.glob("*.json")):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"{path}: invalid json: {exc}")
        ok = False
        continue
    missing = required_keys - data.keys()
    if missing:
        print(f"{path}: missing keys: {', '.join(sorted(missing))}")
        ok = False

if not ok:
    sys.exit(1)

print("tool contract validation ok")
