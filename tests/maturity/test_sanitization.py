import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class MaturitySanitizationTests(unittest.TestCase):
    def test_sanitizes_paths_secrets_and_control_characters(self):
        with tempfile.TemporaryDirectory(prefix="sister-maturity-sanitize-") as temporary:
            results = Path(temporary) / "results.tsv"
            destination = Path(temporary) / "status.json"
            with results.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
                writer.writerow([
                    "FAIL",
                    "pre-alpha",
                    "safe-check",
                    "yes",
                    "Check sanitizado",
                    f"falha em {ROOT}/private.txt cookie=sister_session-value\x01",
                ])
            command = [
                "python3", str(ROOT / "scripts" / "maturity" / "sanitize-attestation.py"),
                "--results", str(results), "--destination", str(destination),
                "--repository", str(ROOT), "--target-stage", "pre-alpha", "--result", "FAIL",
                "--generated-at", "2026-07-31T13:30:00Z", "--verifier-version", "1.0.0",
                "--commit", "0123456789abcdef0123456789abcdef01234567", "--branch", "main",
                "--dirty", "true", "--total", "1", "--passed", "0", "--failed", "1",
                "--warned", "0", "--skipped", "0", "--mandatory-failures", "1",
            ]
            subprocess.run(command, check=True, cwd=ROOT)
            serialized = destination.read_text(encoding="utf-8")
            payload = json.loads(serialized)
            self.assertNotIn(str(ROOT), serialized)
            self.assertNotIn("sister_session-value", serialized)
            self.assertNotIn("\x01", serialized)
            self.assertEqual(payload["blockers"][0]["id"], "safe-check")
            self.assertLessEqual(len(payload["blockers"][0]["detail"]), 500)


if __name__ == "__main__":
    unittest.main()
