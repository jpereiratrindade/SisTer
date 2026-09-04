#!/usr/bin/env python3
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def main():
    schema_path = ROOT / "contracts/ecosystem-semantic/1.0.0/semantic-view.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    sample = {
        "schema": "sister.semantic-ecosystem-view/1.0.0",
        "source_status": "authoritative",
        "source_revision": "fixture-r1",
        "participants": [{
            "participant_id": "participant_alpha",
            "label": "Alpha",
            "declared_state": "active",
            "authority_scope": "alpha-owner",
            "provenance_ref": "urn:test:alpha:r1",
            "capabilities": [{
                "capability_id": "alpha.work.execute",
                "label": "Executar trabalho Alpha",
                "authority_scope": "alpha-owner",
            }],
        }],
        "relations": [],
        "relations_status": "not_available",
    }
    assert list(validator.iter_errors(sample)) == []

    invalid = dict(sample)
    invalid["relations"] = [{"from": "participant_alpha", "to": "participant_beta"}]
    assert list(validator.iter_errors(invalid)), "relations must fail closed"
    print("semantic_ecosystem_contract_tests ok")


if __name__ == "__main__":
    main()
