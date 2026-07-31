import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class MaturityDashboardSmokeTests(unittest.TestCase):
    def test_dashboard_uses_admin_api_and_safe_dom_updates(self):
        source = (ROOT / "web" / "maturity" / "app.js").read_text(encoding="utf-8")
        self.assertIn("/api/admin/maturity/latest", source)
        self.assertIn("/api/admin/maturity/history", source)
        self.assertIn("textContent", source)
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("/api/admin/maturity/run", source)

    def test_dashboard_has_all_status_labels(self):
        source = (ROOT / "web" / "maturity" / "index.html").read_text(encoding="utf-8")
        for label in ("Aprovados", "Falhas", "Advertências", "Ignorados", "Bloqueios"):
            self.assertIn(label, source)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_javascript_syntax(self):
        subprocess.run(["node", "--check", str(ROOT / "web" / "maturity" / "app.js")], check=True)

    def test_application_smoke_script_syntax(self):
        subprocess.run(["bash", "-n", str(ROOT / "scripts" / "app" / "smoke.sh")], check=True)


if __name__ == "__main__":
    unittest.main()
