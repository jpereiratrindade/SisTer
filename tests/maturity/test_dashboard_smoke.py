import os
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
        self.assertIn("/api/admin/maturity/catalog", source)
        self.assertIn("/api/admin/maturity/quality", source)
        self.assertIn('activatePanel("evidence")', source)
        self.assertIn("fetchPublishedJson", source)
        self.assertIn("textContent", source)
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("/api/admin/maturity/run", source)

    def test_dashboard_has_all_status_labels(self):
        source = (ROOT / "web" / "maturity" / "index.html").read_text(encoding="utf-8")
        for label in (
            "Centro de Engenharia do SisTer",
            "Síntese do gate",
            "Camadas avaliadas nesta execução",
            "Resultado técnico do componente",
            "Promoção do componente",
            "O que significa testar SisTer Core?",
            "Gates de engenharia",
            "Testes disponíveis nos perfis versionados",
            "Como ler os testes do SGE",
            "Resultados dos testes de qualidade",
            "legacy",
            "declarative",
            "compare",
            "Saúde da Engenharia",
            "Componentes do Ecossistema",
            "Árvore de decisão",
            "Publicar nova atestação",
            "./scripts/sge maturity publish-all",
            "Aprovados",
            "Falhas",
            "Advertências",
            "Ignorados",
            "Bloqueios",
        ):
            self.assertIn(label, source)

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_javascript_syntax(self):
        subprocess.run(["node", "--check", str(ROOT / "web" / "maturity" / "app.js")], check=True)

    def test_application_smoke_script_syntax(self):
        subprocess.run(["bash", "-n", str(ROOT / "scripts" / "app" / "smoke.sh")], check=True)
        subprocess.run(["bash", "-n", str(ROOT / "scripts" / "maturity" / "run-and-publish.sh")], check=True)
        subprocess.run(["python3", "-m", "py_compile", str(ROOT / "scripts" / "quality" / "run.py")], check=True)

    def test_internal_publisher_rejects_direct_use(self):
        environment = os.environ.copy()
        environment.pop("SGE_INTERNAL_PUBLISH", None)
        completed = subprocess.run(
            [str(ROOT / "scripts" / "maturity" / "run-and-publish.sh"), "pre-alpha"],
            cwd=ROOT, env=environment, text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("./scripts/sge maturity publish", completed.stderr)


if __name__ == "__main__":
    unittest.main()
