import contextlib
import importlib.util
import importlib.machinery
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts" / "validate_local_resources.py"
SPEC = importlib.util.spec_from_file_location("sister_local_resources", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
RESOURCES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESOURCES)
SGE_LOADER = importlib.machinery.SourceFileLoader("sister_sge", str(ROOT / "scripts/sge"))
SGE_SPEC = importlib.util.spec_from_loader(SGE_LOADER.name, SGE_LOADER)
assert SGE_SPEC is not None
SGE = importlib.util.module_from_spec(SGE_SPEC)
SGE_LOADER.exec_module(SGE)


def legacy_configuration() -> dict[str, str]:
    values = {}
    for line in (ROOT / ".sister" / "maturity.conf").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            values[name] = value
    return values


class SgeConvergenceTests(unittest.TestCase):
    def test_engines_share_existing_baseline_and_smoke_scripts(self) -> None:
        legacy = legacy_configuration()
        declarative = yaml.safe_load(
            (ROOT / "engineering/maturity/profiles/sister-core.yaml").read_text(encoding="utf-8")
        )["scripts"]
        pairs = (
            (legacy["VERIFY_IDENTICAL"], declarative["baseline.verify"]["path"]),
            (legacy["SMOKE_TEST"], declarative["ci.test-smoke"]["path"]),
        )
        for legacy_path, declarative_path in pairs:
            self.assertEqual(legacy_path, declarative_path)
            self.assertTrue((ROOT / legacy_path).is_file(), legacy_path)
        self.assertEqual("scripts/ci/test-smoke.sh", legacy["SMOKE_TEST"])

    def test_local_resources_do_not_register_real_subsystems(self) -> None:
        registry = json.loads(
            (ROOT / "config/local_resources.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {"sister", "sister_reference"},
            {project["id"] for project in registry["projects"]},
        )

    def test_resource_validator_rejects_real_subsystem_registration(self) -> None:
        registry = json.loads(
            (ROOT / "config/local_resources.json").read_text(encoding="utf-8")
        )
        registry["projects"].append({
            "id": "sister_campo",
            "repository": "cpp/SisTer-Campo",
            "integrates_with_sister": True,
            "resources": []
        })
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "local_resources.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with mock.patch.object(RESOURCES, "REGISTRY", path), self.assertRaises(SystemExit):
                with contextlib.redirect_stderr(io.StringIO()):
                    RESOURCES.main()

    def test_publish_all_does_not_resolve_quarantined_components(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ecosystem = root / "engineering/maturity/ecosystem.yaml"
            ecosystem.parent.mkdir(parents=True)
            ecosystem.write_text(
                "components:\n"
                "  - id: sister_nexo\n"
                "    governance_status: quarantined\n",
                encoding="utf-8",
            )
            args = type("Args", (), {"stage": None, "engine": None})()
            output = io.StringIO()
            with mock.patch.object(SGE, "ROOT", root), mock.patch.object(
                SGE, "run_internal_publisher"
            ) as publisher, mock.patch.object(
                SGE, "cmd_maturity_components", return_value=0
            ), contextlib.redirect_stdout(output):
                self.assertEqual(0, SGE.cmd_maturity_publish_all(args))
            publisher.assert_not_called()
            self.assertIn("QUARANTINED sister_nexo", output.getvalue())


if __name__ == "__main__":
    unittest.main()
