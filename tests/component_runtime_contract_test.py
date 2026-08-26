#!/usr/bin/env python3
import json
from pathlib import Path
import unittest

import jsonschema
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "contracts" / "component" / "1.0.0"
RUNTIME = ROOT / "contracts" / "runtime" / "1.0.0"
EXAMPLES = COMPONENT / "examples"


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


class ComponentRuntimeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.component_schema = load(COMPONENT / "component.schema.json")
        cls.runtime_schema = load(RUNTIME / "runtime.schema.json")

        cls.registry = Registry().with_resources(
            (
                schema["$id"],
                Resource.from_contents(schema),
            )
            for schema in (cls.component_schema, cls.runtime_schema)
        )

        cls.component_validator = jsonschema.Draft202012Validator(
            cls.component_schema,
            registry=cls.registry,
        )
        cls.runtime_validator = jsonschema.Draft202012Validator(
            cls.runtime_schema,
            registry=cls.registry,
        )

    def test_schemas_are_valid_and_normative(self):
        for schema in (self.component_schema, self.runtime_schema):
            jsonschema.Draft202012Validator.check_schema(schema)
            self.assertEqual("NORMATIVE", schema["x-sister-contract-status"])
            self.assertIs(True, schema["x-sister-runtime-normative"])

    def test_valid_system_component(self):
        self.component_validator.validate(load(EXAMPLES / "valid-system.json"))

    def test_valid_source_only_control_plane(self):
        self.component_validator.validate(
            load(EXAMPLES / "valid-control-plane.json")
        )

    def test_binding_is_not_component_authority(self):
        invalid = load(EXAMPLES / "invalid-with-binding.json")
        self.assertTrue(list(self.component_validator.iter_errors(invalid)))

        forbidden = {
            "address",
            "binding",
            "gateway_host",
            "host",
            "listen_address",
            "listen_port",
            "port",
            "protocol",
            "public_url",
            "socket",
            "transport",
            "url",
        }
        self.assertFalse(property_names(self.component_schema) & forbidden)
        self.assertFalse(property_names(self.runtime_schema) & forbidden)

    def test_runtime_contract_is_transport_neutral(self):
        self.assertNotIn(
            "probes",
            self.runtime_schema["properties"],
        )

        serialized = json.dumps(
            self.runtime_schema,
            sort_keys=True,
        ).lower()

        for transport_term in (
            "http-get",
            "tcp",
            "websocket",
        ):
            self.assertNotIn(
                transport_term,
                serialized,
            )

    def test_build_does_not_accept_arbitrary_shell_commands(self):
        invalid = load(EXAMPLES / "invalid-shell-command.json")
        self.assertTrue(list(self.component_validator.iter_errors(invalid)))

        forbidden = {"command", "shell", "script"}
        self.assertFalse(property_names(self.component_schema) & forbidden)

    def test_paths_cannot_escape_repository(self):
        invalid = load(EXAMPLES / "invalid-parent-entrypoint.json")
        self.assertTrue(list(self.component_validator.iter_errors(invalid)))

    def test_runtime_actions_are_typed(self):
        invalid = load(EXAMPLES / "invalid-runtime-action.json")
        self.assertTrue(
            list(self.component_validator.iter_errors(invalid))
        )

        valid_runtime = load(EXAMPLES / "valid-system.json")["runtime"]
        self.runtime_validator.validate(valid_runtime)

        required_actions = {
            "start",
            "stop",
            "restart",
            "status",
            "health",
        }

        self.assertTrue(
            required_actions.issubset(set(valid_runtime["actions"]))
        )

    def test_health_is_required_and_readiness_is_optional(self):
        valid_runtime = load(EXAMPLES / "valid-system.json")["runtime"]

        self.assertIn("health", valid_runtime["actions"])
        self.assertIn("readiness", valid_runtime["actions"])

        without_health = json.loads(json.dumps(valid_runtime))
        without_health["actions"].remove("health")

        self.assertTrue(
            list(self.runtime_validator.iter_errors(without_health))
        )

        without_readiness = json.loads(json.dumps(valid_runtime))
        without_readiness["actions"].remove("readiness")

        self.runtime_validator.validate(without_readiness)

    def test_component_does_not_self_authorize_deployment(self):
        self.assertNotIn(
            "eligibility",
            property_names(self.component_schema),
        )

        invalid = load(EXAMPLES / "valid-system.json")
        invalid["eligibility"] = {
            "workstation": True,
            "production": True,
        }

        self.assertTrue(
            list(self.component_validator.iter_errors(invalid))
        )

    def test_official_component_consumes_resolved_binding(self):
        descriptor = load(ROOT / ".sister" / "component.json")
        self.component_validator.validate(descriptor)

        runtime = (ROOT / descriptor["runtime"]["entrypoint"]).read_text()
        self.assertIn("SISTER_RESOLVED_DEPLOYMENT_FILE", runtime)
        self.assertIn(".components[] | select(.system_id == $id)", runtime)
        self.assertIn("SISTER_COMPONENT_CONFIG_FILE", runtime)



if __name__ == "__main__":
    unittest.main()
