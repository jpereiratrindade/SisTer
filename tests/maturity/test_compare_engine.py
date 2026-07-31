import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "maturity"))
MODULE_PATH = ROOT / "scripts" / "maturity" / "evaluate-engine.py"
SPEC = importlib.util.spec_from_file_location("evaluate_engine", MODULE_PATH)
evaluate_engine = importlib.util.module_from_spec(SPEC)
sys.modules["evaluate_engine"] = evaluate_engine
SPEC.loader.exec_module(evaluate_engine)


def minimal_payload():
    stages = []
    for stage in ("pre-alpha", "alpha", "beta", "gamma", "production"):
        checks = []
        if stage == "pre-alpha":
            checks = [
                {
                    "id": "unit-tests",
                    "status": "PASS",
                    "mandatory": True,
                    "description": "Unit tests pass",
                    "detail": "ok",
                    "evidence": [],
                }
            ]
        stages.append({"id": stage, "label": stage, "state": "approved", "checks": checks})
    return {
        "schema": "sister.maturity-status/1.0.0",
        "project": "SisTer",
        "target_stage": "pre-alpha",
        "result": "PASS",
        "generated_at": "2026-07-31T00:00:00Z",
        "verifier_version": "1.0.0",
        "source": {"commit": "0" * 40, "short_commit": "0" * 7, "branch": "main", "dirty": False},
        "summary": {"total": 1, "passed": 1, "failed": 0, "warned": 0, "skipped": 0, "mandatory_failures": 0},
        "stages": stages,
        "blockers": [],
        "next_actions": ["ok"],
        "attestation": {"available": False, "signed": False, "relative_path": None},
        "promotion": {"applicable": True, "eligible": True, "recommendation": "promote"},
    }


class CompareEngineTests(unittest.TestCase):
    def test_equivalent_payloads_have_no_divergences(self):
        payload = minimal_payload()
        self.assertEqual(evaluate_engine.compare_payloads(payload, copy.deepcopy(payload)), [])

    def test_mandatory_check_status_mismatch_is_blocking_divergence(self):
        legacy = minimal_payload()
        declarative = minimal_payload()
        declarative["stages"][0]["checks"][0]["status"] = "FAIL"
        divergences = evaluate_engine.compare_payloads(legacy, declarative)
        self.assertTrue(any(item["classification"] == "check_status_mismatch" for item in divergences))
        self.assertTrue(all(item["blocking"] for item in divergences))

    def test_missing_check_is_blocking_divergence(self):
        legacy = minimal_payload()
        declarative = minimal_payload()
        declarative["stages"][0]["checks"] = []
        divergences = evaluate_engine.compare_payloads(legacy, declarative)
        self.assertTrue(any(item["classification"] == "check_missing" for item in divergences))
        self.assertTrue(all(item["blocking"] for item in divergences))


if __name__ == "__main__":
    unittest.main()
