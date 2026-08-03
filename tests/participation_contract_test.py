#!/usr/bin/env python3
import json
from pathlib import Path

import jsonschema
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/participation/1.0.0"


def main() -> None:
    schema_path = CONTRACT / "participation-contract.schema.json"
    names = (
        "participation-contract.schema.json",
        "capability-definition.schema.json",
        "contribution-definition.schema.json",
        "authority-allocation.schema.json",
        "boundary-object-envelope.schema.json",
        "participation-assessment.schema.json",
    )
    schemas = [json.loads((CONTRACT / name).read_text(encoding="utf-8")) for name in names]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    schema = schemas[0]
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    valid = json.loads((CONTRACT / "examples/reference-proposed.json").read_text(encoding="utf-8"))
    invalid = json.loads((CONTRACT / "examples/invalid-self-authorized.json").read_text(encoding="utf-8"))
    validator.validate(valid)
    errors = list(validator.iter_errors(invalid))
    assert errors, "self-authorized participation must be rejected"
    assert any(list(error.path) == ["state"] for error in errors)
    envelope_schema = schemas[4]
    assessment_schema = schemas[5]
    jsonschema.Draft202012Validator(envelope_schema, registry=registry).validate(
        json.loads((CONTRACT / "examples/reference-envelope.json").read_text(encoding="utf-8"))
    )
    assessment_validator = jsonschema.Draft202012Validator(assessment_schema, registry=registry)
    assessment_validator.validate(
        json.loads((CONTRACT / "examples/reference-assessment.json").read_text(encoding="utf-8"))
    )
    invalid_assessment = json.loads(
        (CONTRACT / "examples/invalid-assessment-authorizes.json").read_text(encoding="utf-8")
    )
    assert list(assessment_validator.iter_errors(invalid_assessment)), (
        "assessment must not embed an authorization decision"
    )
    for document in schemas:
        jsonschema.Draft202012Validator.check_schema(document)
    print("participation contract validation ok")


if __name__ == "__main__":
    main()
