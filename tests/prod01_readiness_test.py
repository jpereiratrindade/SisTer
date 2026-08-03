#!/usr/bin/env python3
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))
import prod01_readiness as prod01  # noqa: E402


class Prod01ReadinessTests(unittest.TestCase):
    def test_missing_operational_evidence_is_pending(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing.md"
            gate = prod01.operational_evidence("G3", "Operação", path.name, "runbook")
        self.assertEqual(gate.status, "PENDING")

    def test_evidence_requires_explicit_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            evidence_root = ROOT / "docs/evidence/operations"
            target = evidence_root / "PROD-01-test.md"
            target.write_text("Status: PENDING\n", encoding="utf-8")
            try:
                gate = prod01.operational_evidence("G3", "Operação", target.name, "runbook")
                self.assertEqual(gate.status, "BLOCKED")
                target.write_text("status: PASS\n", encoding="utf-8")
                gate = prod01.operational_evidence("G3", "Operação", target.name, "runbook")
                self.assertEqual(gate.status, "PASS")
            finally:
                target.unlink(missing_ok=True)

    def test_report_never_authorizes_production(self):
        with tempfile.TemporaryDirectory() as temporary:
            gates = [prod01.Gate("G1", "Plataforma", "PASS", "ok", [])]
            report = Path(temporary) / "report.json"
            payload = prod01.write_report(report, gates, "a" * 40)
            self.assertEqual(payload["decision"], "AWAITING_AUTHORIZATION")
            self.assertFalse(payload["production_authorized"])
            self.assertEqual(json.loads(report.read_text())["technical_status"], "READY_FOR_PROMOTION")


if __name__ == "__main__":
    unittest.main()
