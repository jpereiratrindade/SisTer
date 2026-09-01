#!/usr/bin/env python3
import copy
import json
from pathlib import Path
import unittest

import jsonschema
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
PARTICIPANT = ROOT / "contracts/participant/2.0.0"
INVOCATION = ROOT / "contracts/capability-invocation/1.0.0"
RELATION = ROOT / "contracts/relation/1.0.0"
SUBSYSTEM = ROOT / "contracts/subsystem/1.0.0"
REFERENCE_MANIFEST = ROOT / "reference/sister-reference/manifest.json"
COMPATIBILITY = (
    ROOT / "contracts/compatibility/SUBSYSTEM_1.0.0_TO_ARC01_DRAFTS.md"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def property_names(document):
    names = set()
    if isinstance(document, dict):
        properties = document.get("properties")
        if isinstance(properties, dict):
            names.update(properties)
        for value in document.values():
            names.update(property_names(value))
    elif isinstance(document, list):
        for value in document:
            names.update(property_names(value))
    return names


class Arc01ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_paths = (
            PARTICIPANT / "capability.schema.json",
            PARTICIPANT / "participant.schema.json",
            INVOCATION / "invocation.schema.json",
            INVOCATION / "invocation-result.schema.json",
            RELATION / "relation.schema.json",
        )
        cls.schemas = {path.name: load(path) for path in cls.schema_paths}
        cls.registry = Registry().with_resources(
            (schema["$id"], Resource.from_contents(schema))
            for schema in cls.schemas.values()
        )

        cls.participant_validator = jsonschema.Draft202012Validator(
            cls.schemas["participant.schema.json"], registry=cls.registry
        )
        cls.invocation_validator = jsonschema.Draft202012Validator(
            cls.schemas["invocation.schema.json"], registry=cls.registry
        )
        cls.result_validator = jsonschema.Draft202012Validator(
            cls.schemas["invocation-result.schema.json"], registry=cls.registry
        )
        cls.relation_validator = jsonschema.Draft202012Validator(
            cls.schemas["relation.schema.json"], registry=cls.registry
        )

        cls.nexo = load(PARTICIPANT / "examples/participant-nexo.json")
        cls.praxis = load(PARTICIPANT / "examples/participant-praxis.json")
        cls.atmos = load(PARTICIPANT / "examples/participant-atmos.json")
        cls.invocation = load(INVOCATION / "examples/nexo-to-praxis.json")
        cls.result = load(INVOCATION / "examples/nexo-to-praxis-result.json")
        cls.relation = load(
            RELATION / "examples/nexo-praxis-method-assessment.json"
        )

    def test_schemas_are_valid_and_explicitly_non_normative(self):
        for schema in self.schemas.values():
            jsonschema.Draft202012Validator.check_schema(schema)
            self.assertEqual(schema["x-sister-contract-status"], "DRAFT")
            self.assertIs(schema["x-sister-runtime-normative"], False)

    def test_valid_examples(self):
        self.participant_validator.validate(self.nexo)
        self.participant_validator.validate(self.praxis)
        self.participant_validator.validate(self.atmos)
        self.invocation_validator.validate(self.invocation)
        self.result_validator.validate(self.result)
        self.relation_validator.validate(self.relation)

        for instance in (
            self.nexo,
            self.praxis,
            self.atmos,
            self.invocation,
            self.result,
            self.relation,
        ):
            self.assertEqual(instance["contract_status"], "DRAFT")
            self.assertIs(instance["runtime_normative"], False)

    def test_semantic_links_do_not_require_a_central_intermediary(self):
        participants = {
            item["participant_id"]: item for item in (self.nexo, self.praxis)
        }
        relation_participants = {
            item["participant_id"] for item in self.relation["participants"]
        }
        self.assertEqual(relation_participants, set(participants))

        grant = self.relation["capability_grants"][0]
        target_capabilities = {
            (item["capability_id"], item["version"])
            for item in participants[grant["target"]]["capabilities"]
        }
        self.assertIn((grant["capability_id"], grant["version"]), target_capabilities)
        self.assertEqual(self.invocation["relation_id"], self.relation["relation_id"])
        self.assertEqual(self.invocation["caller_participant_id"], grant["caller"])
        self.assertEqual(self.invocation["target_participant_id"], grant["target"])
        self.assertEqual(self.invocation["capability"]["capability_id"], grant["capability_id"])
        self.assertEqual(self.invocation["capability"]["version"], grant["version"])
        self.assertEqual(
            self.invocation["subject_assertion"]["audience"], grant["target"]
        )
        self.assertEqual(self.result["invocation_id"], self.invocation["invocation_id"])
        self.assertEqual(self.result["request_id"], self.invocation["request_id"])
        self.assertEqual(self.result["responding_participant_id"], grant["target"])

    def test_binding_details_are_not_contract_fields(self):
        forbidden = {
            "endpoint",
            "haproxy",
            "host",
            "http",
            "mandatory_intermediary",
            "method",
            "path",
            "port",
            "sisterd",
            "transport",
        }
        for schema in self.schemas.values():
            self.assertFalse(
                property_names(schema) & forbidden,
                f"binding detail leaked into {schema['$id']}",
            )

    def test_binding_leak_examples_fail_closed(self):
        invalid_cases = (
            (
                self.participant_validator,
                PARTICIPANT / "examples/invalid-participant-with-transport.json",
            ),
            (
                self.invocation_validator,
                INVOCATION / "examples/invalid-invocation-with-endpoint.json",
            ),
            (
                self.relation_validator,
                RELATION / "examples/invalid-relation-with-intermediary.json",
            ),
        )
        for validator, path in invalid_cases:
            self.assertTrue(list(validator.iter_errors(load(path))), path.name)

    def test_result_exclusivity(self):
        invalid = copy.deepcopy(self.result)
        invalid["error"] = {
            "code": "invalid.dual-result",
            "message": "A successful result cannot also carry an error.",
            "responsible_participant_id": "sister_praxis",
        }
        self.assertTrue(list(self.result_validator.iter_errors(invalid)))

    def test_v1_remains_valid_but_is_not_a_v2_participant(self):
        legacy_schema = load(SUBSYSTEM / "manifest.schema.json")
        legacy_manifest = load(REFERENCE_MANIFEST)
        jsonschema.Draft202012Validator.check_schema(legacy_schema)
        jsonschema.Draft202012Validator(legacy_schema).validate(legacy_manifest)
        self.assertTrue(list(self.participant_validator.iter_errors(legacy_manifest)))

    def test_compatibility_matrix_is_explicit(self):
        matrix = COMPATIBILITY.read_text(encoding="utf-8")
        for required in (
            "DRAFT / NOT RUNTIME-NORMATIVE",
            "sister.subsystem/1.0.0",
            "sister.participant/2.0.0",
            "sister.capability-invocation/1.0.0",
            "sister.relation/1.0.0",
            "Não existe fallback",
            "sem equivalente",
        ):
            self.assertIn(required, matrix)


if __name__ == "__main__":
    unittest.main()
