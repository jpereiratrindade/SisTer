import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "quality" / "finalize_run.py"
SPEC = importlib.util.spec_from_file_location("sister_finalize_run", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
FINALIZE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FINALIZE
SPEC.loader.exec_module(FINALIZE)


class RunSurfaceTests(unittest.TestCase):
    def test_local_profile_has_no_public_gateway(self) -> None:
        FINALIZE.validate_surface("LOCAL_ONLY", "loopback-tcp", "NOT_REQUESTED", None)

    def test_lan_profile_requires_federated_gateway(self) -> None:
        FINALIZE.validate_surface(
            "LAN_FEDERATED", "unix-socket", "READY", "https://sister-gateway.test:8443"
        )
        with self.assertRaises(ValueError):
            FINALIZE.validate_surface("LAN_FEDERATED", "loopback-tcp", "READY", "https://x")
        with self.assertRaises(ValueError):
            FINALIZE.validate_surface("LAN_FEDERATED", "unix-socket", "NOT_REQUESTED", None)

    def test_security_validation_does_not_publish(self) -> None:
        FINALIZE.validate_surface("SECURITY_VALIDATION", "loopback-tcp", "VALIDATED", None)
        with self.assertRaises(ValueError):
            FINALIZE.validate_surface("SECURITY_VALIDATION", "loopback-tcp", "READY", "https://x")


if __name__ == "__main__":
    unittest.main()
