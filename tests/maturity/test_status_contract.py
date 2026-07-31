import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "maturity" / "status_contract.py"
SPEC = importlib.util.spec_from_file_location("status_contract", MODULE_PATH)
status_contract = importlib.util.module_from_spec(SPEC)
sys.modules["status_contract"] = status_contract
SPEC.loader.exec_module(status_contract)


class MaturityStatusContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads(
            (ROOT / "contracts" / "maturity" / "1.0.0" / "example.json").read_text(encoding="utf-8")
        )
        cls.schema = json.loads(
            (ROOT / "contracts" / "maturity" / "1.0.0" / "maturity-status.schema.json").read_text(encoding="utf-8")
        )

    def test_example_matches_schema_and_runtime_validator(self):
        jsonschema.Draft202012Validator.check_schema(self.schema)
        jsonschema.Draft202012Validator(self.schema).validate(self.example)
        self.assertEqual(status_contract.validate_status(self.example), [])

    def test_rejects_absolute_path(self):
        payload = copy.deepcopy(self.example)
        payload["stages"][0]["checks"][0]["detail"] = "/home/user/private/report.txt"
        self.assertIn("unsafe check detail for baseline-integrity", status_contract.validate_status(payload))

    def test_rejects_secret_assignment(self):
        payload = copy.deepcopy(self.example)
        payload["next_actions"] = ["token=not-allowed"]
        self.assertIn("invalid next_actions", status_contract.validate_status(payload))

    def test_rejects_unknown_stage(self):
        payload = copy.deepcopy(self.example)
        payload["target_stage"] = "release-candidate"
        self.assertIn("invalid target_stage", status_contract.validate_status(payload))


if __name__ == "__main__":
    unittest.main()
