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
            gates = [
                prod01.Gate("G1", "Plataforma", "PASS", "ok", []),
                prod01.Gate("G2", "Segurança", "PASS", "ok", []),
                prod01.Gate("G3", "Operação", "PASS", "ok", []),
                prod01.Gate("G4", "Recuperação", "PASS", "ok", []),
                prod01.Gate("G5", "Observabilidade", "PASS", "ok", []),
                prod01.Gate("G6", "Promoção", "AWAITING_AUTHORIZATION", "ok", []),
            ]
            report = Path(temporary) / "report.json"
            payload = prod01.write_report(report, gates, "a" * 40)
            self.assertEqual(payload["decision"], "AWAITING_AUTHORIZATION")
            self.assertFalse(payload["production_authorized"])
            self.assertEqual(json.loads(report.read_text())["technical_status"], "READY")

    def test_promotion_authorization_requires_current_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = prod01.AUTHORIZATION_EVIDENCE
            try:
                auth = Path(temporary) / "PROD-01-G6-authorization.md"
                prod01.AUTHORIZATION_EVIDENCE = auth
                self.assertEqual(prod01.authorization_gate("a" * 40).status, "AWAITING_AUTHORIZATION")

                auth.write_text(self.authorization_text("b" * 40), encoding="utf-8")
                self.assertEqual(prod01.authorization_gate("a" * 40).status, "BLOCKED")

                auth.write_text("Decision: AUTHORIZED\ncommit: {}\n".format("a" * 40), encoding="utf-8")
                self.assertEqual(prod01.authorization_gate("a" * 40).status, "BLOCKED")

                auth.write_text(self.authorization_text("a" * 40), encoding="utf-8")
                self.assertEqual(prod01.authorization_gate("a" * 40).status, "AUTHORIZED")
            finally:
                prod01.AUTHORIZATION_EVIDENCE = original

    def test_authorized_report_updates_promotion_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            gates = [
                prod01.Gate("G1", "Plataforma", "PASS", "ok", []),
                prod01.Gate("G2", "Segurança", "PASS", "ok", []),
                prod01.Gate("G3", "Operação", "PASS", "ok", []),
                prod01.Gate("G4", "Recuperação", "PASS", "ok", []),
                prod01.Gate("G5", "Observabilidade", "PASS", "ok", []),
                prod01.Gate("G6", "Promoção", "AUTHORIZED", "ok", []),
            ]
            report = Path(temporary) / "readiness.json"
            promotion = Path(temporary) / "promotion.md"
            core_state = Path(temporary) / "core-state.json"
            payload = prod01.write_report(report, gates, "a" * 40)
            prod01.write_promotion_artifacts(promotion, core_state, payload)

            self.assertEqual(payload["technical_status"], "READY")
            self.assertEqual(payload["decision"], "AUTHORIZED")
            self.assertTrue(payload["production_authorized"])
            self.assertEqual(payload["promotion"]["mvp_version"], "v0.1.0")
            self.assertEqual(payload["promotion"]["tag"], "prod-mvp-v0.1.0")
            self.assertEqual(payload["promotion"]["product_maturity"], "Beta")
            self.assertEqual(payload["promotion"]["operational_state"], "Produção MVP")
            self.assertIn("Produção MVP", promotion.read_text(encoding="utf-8"))
            self.assertIn("MVP version: `v0.1.0`", promotion.read_text(encoding="utf-8"))
            self.assertIn("Product maturity: `Beta`", promotion.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(core_state.read_text(encoding="utf-8"))["state"], "Produção MVP")
            self.assertEqual(json.loads(core_state.read_text(encoding="utf-8"))["mvp_version"], "v0.1.0")
            self.assertEqual(json.loads(core_state.read_text(encoding="utf-8"))["product_maturity"], "Beta")

    def authorization_text(self, commit):
        return "\n".join([
            "Decision: AUTHORIZED",
            f"commit: {commit}",
            "release: v0.1.0",
            "git_tag: prod-mvp-v0.1.0",
            "authorized_by: owner",
            "authorized_at: 2026-08-03T00:00:00Z",
            "rollback_reference: docs/evidence/operations/PROD-01-G4-recovery.md",
            "known_limitations: MVP scope",
            "",
        ])


if __name__ == "__main__":
    unittest.main()
