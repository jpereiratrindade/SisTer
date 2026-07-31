import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SgeCliTests(unittest.TestCase):
    def test_help_lists_maturity_commands(self):
        proc = subprocess.run(
            [str(ROOT / "scripts" / "sge"), "maturity", "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("evaluate", proc.stdout)
        self.assertIn("publish", proc.stdout)
        self.assertIn("validate", proc.stdout)

    def test_contract_validation_command_passes(self):
        subprocess.run(
            [str(ROOT / "scripts" / "sge"), "maturity", "validate"],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
