#!/usr/bin/env python3
import json
from pathlib import Path
from jsonschema import Draft202012Validator

root = Path(__file__).resolve().parents[2]
base = root / "contracts/federation/1.0.0"
schema = json.loads((base / "federated-system-manifest.schema.json").read_text())
Draft202012Validator.check_schema(schema)
example = json.loads((base / "example.json").read_text())
errors = list(Draft202012Validator(schema).iter_errors(example))
if errors:
    raise SystemExit("[FAIL] " + "; ".join(error.message for error in errors))
print("[OK] FED-01 schema and example are valid")
print("[OK] operational status, maturity and capabilities are explicit")
