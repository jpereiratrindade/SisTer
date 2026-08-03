#!/usr/bin/env python3
"""Validate the REF-00 schemas, examples, references and shadow invariants."""
import json
import sys
import warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=DeprecationWarning, module="jsonschema")
from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "contracts/reflexivity/1.0.0"
EXAMPLES = BASE / "examples"

def load(name):
    return json.loads((BASE / name).read_text())

def validate(schema_name, instance_name):
    schema = load(schema_name)
    instance = json.loads((EXAMPLES / instance_name).read_text())
    resolver = RefResolver(schema["$id"], schema, store={
        load("evidence-reference.schema.json")["$id"]: load("evidence-reference.schema.json")
    })
    errors = sorted(Draft202012Validator(schema, resolver=resolver).iter_errors(instance), key=str)
    if errors:
        raise AssertionError(f"{instance_name}: " + "; ".join(e.message for e in errors))
    return instance

def validate_shadow_policy(instance):
    if instance.get("gate_effect") != "shadow":
        raise AssertionError("shadow profile cannot select a non-shadow gate")
    if instance.get("proposed_action") != "none":
        raise AssertionError("shadow profile cannot propose a corrective action")
    if instance.get("operational_effect") != "none":
        raise AssertionError("shadow profile cannot have an operational effect")

def main():
    profile = validate("reflexivity-profile.schema.json", "rfp-nc-01.json")
    snapshot = validate("reference-snapshot.schema.json", "reference-snapshot-example.json")
    positives = ["assessment-confirmed.json", "assessment-divergent.json",
                 "assessment-inconclusive.json", "assessment-not-applicable.json"]
    for name in positives:
        assessment = validate("operational-assessment.schema.json", name)
        validate_shadow_policy(assessment)

    assert profile["depth"] == ["D2", "D3"]
    assert profile["authority"] == "A1"
    assert profile["mode"] == "shadow"
    assert profile["gate_effect"] == "shadow"
    assert profile["allowed_actions"] == []
    assert profile["automatic_correction"] is False
    assert snapshot["references"][0]["digest"]

    for name in ["invalid-shadow-with-block-effect.json", "invalid-shadow-with-corrective-action.json"]:
        instance = json.loads((EXAMPLES / name).read_text())
        try:
            validate_shadow_policy(validate("operational-assessment.schema.json", name))
        except AssertionError:
            continue
        raise AssertionError(f"{name}: expected rejection")
    try:
        validate("reference-snapshot.schema.json", "invalid-reference-without-digest.json")
    except AssertionError:
        pass
    else:
        raise AssertionError("invalid-reference-without-digest.json: expected rejection")
    print("[OK] REF-00 schemas, references, positive examples and negative examples")
    print("[OK] RFP-NC-01 D2-D3/A1/shadow has no operational effect or corrective action")

if __name__ == "__main__":
    try:
        main()
    except (AssertionError, json.JSONDecodeError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        sys.exit(1)
