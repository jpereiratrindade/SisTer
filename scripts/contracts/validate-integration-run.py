#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "contracts/execution/1.0.0"
EXAMPLES = BASE / "examples"

def check(name):
    schema = json.loads((BASE / "integration-run.schema.json").read_text())
    instance_path = BASE / name if name == "example.json" else EXAMPLES / name
    instance = json.loads(instance_path.read_text())
    errors = list(Draft202012Validator.check_schema(schema) or []) if False else list(Draft202012Validator(schema).iter_errors(instance))
    if errors:
        raise AssertionError(f"{name}: " + "; ".join(e.message for e in errors))
    return instance

def main():
    schema = json.loads((BASE / "integration-run.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    positives = ["example.json", "integration-run-proposed.json", "integration-run-running.json", "integration-run-failed.json", "integration-run-cancelled.json", "integration-run-superseded.json"]
    for name in positives:
        check(name)
    negatives = ["invalid-completed-without-output.json", "invalid-failed-without-error.json", "invalid-running-with-finished-at.json", "invalid-retry-without-parent-run.json"]
    for name in negatives:
        try:
            check(name)
        except AssertionError:
            continue
        raise AssertionError(f"{name}: expected rejection")
    example = check("example.json")
    assert example["execution_status"] == "completed"
    assert example["validity_status"] == "pending"
    assert example["outputs"] and example["finished_at"]
    print("[OK] EXEC-01 schema and references are valid")
    print("[OK] positive lifecycle examples accepted")
    print("[OK] prohibited lifecycle combinations rejected")
    print("[OK] execution_status and validity_status remain independent")

if __name__ == "__main__":
    try:
        main()
    except (AssertionError, json.JSONDecodeError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        sys.exit(1)
