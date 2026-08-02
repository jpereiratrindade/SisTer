import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "resolve_run_profile.py"
SPEC = importlib.util.spec_from_file_location("sister_run_profiles", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROFILES = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROFILES
SPEC.loader.exec_module(PROFILES)


class RunProfileTests(unittest.TestCase):
    def test_profiles_are_executable_contracts(self) -> None:
        profiles = PROFILES.load_profiles()
        self.assertEqual("none", profiles["dev-core"]["subsystems"]["selection"])
        self.assertEqual("all", profiles["dev-ecosystem"]["subsystems"]["selection"])

    def test_sec03v_requires_real_gateway_and_nexo(self) -> None:
        profile = PROFILES.load_profiles()["sec-03v"]
        self.assertEqual("required", profile["gateway_dynamic_tests"])
        self.assertEqual(["sister_nexo"], profile["subsystems"]["required"])
        self.assertFalse(profile["gate_closure_authorized"])


if __name__ == "__main__":
    unittest.main()
