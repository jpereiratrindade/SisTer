#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts/engineering/planning/1.0.0"


def main():
    errors = []
    schemas = {}
    for path in sorted(CONTRACT.glob("*.schema.json")):
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            jsonschema.Draft7Validator.check_schema(schema)
            schemas[schema["$id"]] = schema
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    plan_path = ROOT / "engineering/planning/plan.json"
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if plan.get("schema") != "sister.plan/1.0.0":
            errors.append(f"{plan_path}: invalid plan schema")
        goal = plan["goal"]
        gap = plan["gaps"][0]
        action = plan["actions"][0]
        jsonschema.validate(goal, schemas["https://sister.local/schemas/engineering/planning/1.0.0/development-goal.schema.json"])
        jsonschema.validate(gap, schemas["https://sister.local/schemas/engineering/planning/1.0.0/development-gap.schema.json"])
        jsonschema.validate(action, schemas["https://sister.local/schemas/engineering/planning/1.0.0/development-action.schema.json"])
        if action["goal_id"] != goal["goal_id"] or action["gap_id"] != gap["gap_id"]:
            errors.append("plan: goal/gap/action chain is inconsistent")
    except Exception as exc:
        errors.append(f"{plan_path}: {exc}")
    if errors:
        print("planning contract validation failed")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("planning contract validation ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
