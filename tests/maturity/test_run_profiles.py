import importlib.util
from pathlib import Path
import sys
import subprocess
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
        self.assertEqual(
            {"dev-core", "dev-reference", "dev-lan", "test-core", "sec-03v"},
            set(profiles),
        )
        self.assertEqual("none", profiles["dev-core"]["subsystems"]["selection"])
        self.assertEqual("listed", profiles["dev-reference"]["subsystems"]["selection"])
        self.assertEqual(["sister_reference"], profiles["dev-reference"]["subsystems"]["projects"])
        self.assertEqual("LOCAL_ONLY", profiles["dev-reference"]["access_scope"])
        self.assertEqual("not-requested", profiles["dev-reference"]["public_gateway"])

    def test_dev_lan_uses_only_federated_gateway(self) -> None:
        profile = PROFILES.load_profiles()["dev-lan"]
        self.assertEqual("LAN_FEDERATED", profile["access_scope"])
        self.assertEqual("unix-socket", profile["core_transport"])
        self.assertEqual("lan-required", profile["public_gateway"])
        self.assertEqual("required", profile["gateway_dynamic_tests"])

    def test_sec03v_requires_real_gateway_and_reference(self) -> None:
        profile = PROFILES.load_profiles()["sec-03v"]
        self.assertEqual("required", profile["gateway_dynamic_tests"])
        self.assertEqual(["sister_reference"], profile["subsystems"]["required"])
        self.assertFalse(profile["gate_closure_authorized"])

    def test_reference_profile_blocks_any_failure(self) -> None:
        profile = PROFILES.load_profiles()["dev-reference"]
        self.assertEqual(["sister_reference"], profile["subsystems"]["projects"])
        self.assertEqual("block", profile["subsystems"]["failure_policy"])

    def test_managed_execution_uses_postgresql_authentication(self) -> None:
        serve = (ROOT / "scripts" / "app" / "serve.sh").read_text(encoding="utf-8")
        lan = (ROOT / "scripts" / "run_gateway_lan_lab.sh").read_text(encoding="utf-8")

        self.assertIn('SISTER_AUTH_BACKEND="${SISTER_AUTH_BACKEND:-postgresql}"', serve)
        self.assertIn('SISTER_AUTH_BACKEND=postgresql', lan)
        self.assertNotIn('sync-runtime "$RUN_DIR/auth-users.tsv"', lan)
        self.assertNotIn('SISTER_AUTH_FILE="$RUN_DIR/auth-users.tsv"', lan)

    def test_environment_summary_redacts_database_credentials(self) -> None:
        completed = subprocess.run(
            [
                "bash",
                "-c",
                "source scripts/lib/sister_env.sh; "
                "export SISTER_DATABASE_URL='postgresql://user:unique-secret@localhost/db'; "
                "export SISTER_ENV=dev COMPOSE_PROJECT_NAME=x SISTER_DB_CONTAINER=x "
                "SISTER_DB_PORT=1 SISTER_DB_VOLUME=x SISTER_APP_PORT=2 "
                "SISTER_BIND_HOST=127.0.0.1; sister_print_env",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertNotIn("unique-secret", completed.stdout)
        self.assertIn("credentials redacted", completed.stdout)


if __name__ == "__main__":
    unittest.main()
