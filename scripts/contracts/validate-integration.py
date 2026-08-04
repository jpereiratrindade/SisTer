#!/usr/bin/env python3
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)
from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "contracts/integration/1.0.0"
EXAMPLES = BASE / "examples"


def load_schema(name):
    return json.loads((BASE / name).read_text())


def validate(schema_name, example_name):
    schema = load_schema(schema_name)
    store = {
        load_schema("capability-offer.schema.json")["$id"]: load_schema("capability-offer.schema.json")
    }
    resolver = RefResolver(schema["$id"], schema, store=store)
    instance = json.loads((EXAMPLES / example_name).read_text())
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema, resolver=resolver).iter_errors(instance), key=str)
    if errors:
        raise AssertionError(f"{example_name}: " + "; ".join(error.message for error in errors))
    return instance


def main():
    offer = validate("capability-offer.schema.json", "capability-offer-reference.json")
    requirement = validate("capability-requirement.schema.json", "capability-requirement-sister.json")
    definition = validate("integration-definition.schema.json", "integration-definition-reference.json")
    decision = validate("integration-decision.schema.json", "integration-decision-approve-reference.json")
    execution = validate("integration-execution.schema.json", "integration-execution-reference.json")
    assessment = validate("operational-assessment.schema.json", "operational-assessment-reference.json")

    assert definition["offer_id"] == offer["offer_id"]
    assert definition["requirement_id"] == requirement["requirement_id"]
    assert offer["subsystem_id"] == "sister_reference"
    assert definition["approval"]["status"] == "draft"
    assert decision["integration_id"] == definition["integration_id"]
    assert decision["integration_version"] == definition["version"]
    assert decision["authority"] == "integration.approve"
    assert execution["integration_id"] == definition["integration_id"]
    assert execution["status"] == "completed"
    assert execution.get("outputs")
    assert assessment["execution_id"] == execution["execution_id"]
    assert assessment["integration_id"] == definition["integration_id"]

    print("[OK] integration schemas and examples are valid")
    print("[OK] reference system offer -> SisTer requirement -> definition -> decision -> execution -> assessment links are consistent")
    print("[OK] draft integration is valid but does not promote an approved capability")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, json.JSONDecodeError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        sys.exit(1)
