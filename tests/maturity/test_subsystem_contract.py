import json
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts" / "subsystem" / "1.0.0"
EXAMPLES = CONTRACT / "examples"


class SubsystemContractTests(unittest.TestCase):
    def load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def validator(self, name):
        schema = self.load(CONTRACT / name)
        jsonschema.Draft202012Validator.check_schema(schema)
        return jsonschema.Draft202012Validator(schema)

    def test_required_alpha_artifacts_exist(self):
        for name in (
            "manifest.schema.json",
            "capabilities.schema.json",
            "identity-claims.schema.json",
            "identity.schema.json",
            "echo.schema.json",
            "health.schema.json",
            "readiness.schema.json",
            "error.schema.json",
            "audit-event.schema.json",
            "openapi.yaml",
            "README.md",
        ):
            self.assertTrue((CONTRACT / name).is_file(), name)

    def test_reference_implements_manifest_contract(self):
        validator = self.validator("manifest.schema.json")
        manifest = self.load(ROOT / "reference/sister-reference/manifest.json")
        validator.validate(manifest)
        self.assertEqual("sister.subsystem/1.0.0", manifest["contract"])
        self.assertEqual("/integrations/reference/", manifest["mount_path"])
        self.assertEqual("/health", manifest["technical_endpoints"]["health"])

    def test_examples_validate_against_their_schemas(self):
        pairs = (
            ("error.schema.json", "error.json"),
            ("audit-event.schema.json", "audit-event.json"),
            ("identity-claims.schema.json", "identity-claims.json"),
        )
        for schema_name, example_name in pairs:
            with self.subTest(example=example_name):
                self.validator(schema_name).validate(self.load(EXAMPLES / example_name))

    def test_openapi_references_contract_schemas(self):
        source = (CONTRACT / "openapi.yaml").read_text(encoding="utf-8")
        for name in ("manifest.schema.json", "health.schema.json", "readiness.schema.json", "capabilities.schema.json", "identity.schema.json", "echo.schema.json"):
            self.assertIn(name, source)
        for path in ("/manifest", "/health", "/ready", "/capabilities", "/identity", "/echo"):
            self.assertIn(path, source)


if __name__ == "__main__":
    unittest.main()
