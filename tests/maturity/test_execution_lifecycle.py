import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "app" / "execution_lifecycle.py"
SPEC = importlib.util.spec_from_file_location("sister_execution_lifecycle", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
LIFECYCLE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LIFECYCLE
SPEC.loader.exec_module(LIFECYCLE)


class ExecutionLifecycleTests(unittest.TestCase):
    def test_begin_records_preexisting_containers_privately(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executions = Path(temporary) / "executions"
            args = argparse.Namespace(
                profile="dev-ecosystem", environment="dev", access_scope="LOCAL_ONLY"
            )
            with mock.patch.object(LIFECYCLE, "ROOT", Path(temporary)), mock.patch.object(
                LIFECYCLE, "EXECUTIONS", executions
            ), mock.patch.object(LIFECYCLE, "running_containers", return_value={"existing-db"}):
                LIFECYCLE.begin(args)
            state = executions / "active-dev.json"
            payload = json.loads(state.read_text())
            self.assertEqual(["existing-db"], payload["containers_before"])
            self.assertEqual("STARTING", payload["status"])
            self.assertEqual(0o600, state.stat().st_mode & 0o777)

    def test_finalize_classifies_owned_and_reused_resources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executions = Path(temporary) / "executions"
            executions.mkdir()
            state = executions / "active-dev.json"
            state.write_text(json.dumps({
                "schema": "sister.execution-state/1.0.0",
                "containers_before": ["existing-db"],
            }))
            report = Path(temporary) / "subsystems.json"
            report.write_text(json.dumps({"components": [{
                "component": "sister_reference", "started_by_run": True, "process_group": 1234
            }]}))
            args = argparse.Namespace(environment="dev", subsystems_report=report)
            with mock.patch.object(LIFECYCLE, "EXECUTIONS", executions), mock.patch.object(
                LIFECYCLE, "ROOT", Path(temporary)
            ), mock.patch.object(
                LIFECYCLE, "running_containers", return_value={"existing-db", "new-db"}
            ), mock.patch.object(
                LIFECYCLE, "candidate_containers", return_value={"existing-db", "new-db"}
            ):
                LIFECYCLE.finalize(args)
            payload = json.loads(state.read_text())
            self.assertEqual(["new-db"], payload["owned_containers"])
            self.assertEqual(["existing-db"], payload["reused_containers"])
            self.assertEqual([{"component": "sister_reference", "pgid": 1234}], payload["owned_process_groups"])

    def test_stop_marks_owned_groups_and_uses_component_only_gateway_stop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executions = root / ".run" / "executions"
            executions.mkdir(parents=True)
            state = executions / "active-dev.json"
            state.write_text(json.dumps({
                "schema": "sister.execution-state/1.0.0",
                "execution_id": "test-execution",
                "profile": "dev-lan",
                "environment": "dev",
                "status": "RUNNING",
                "owned_process_groups": [{"component": "sister_reference", "pgid": 1234}],
                "owned_processes": {"gateway": 2345, "gateway_sisterd": 3456},
                "owned_containers": [],
                "reused_containers": [],
            }))
            args = argparse.Namespace(environment="dev")
            with mock.patch.object(LIFECYCLE, "ROOT", root), mock.patch.object(
                LIFECYCLE, "EXECUTIONS", executions
            ), mock.patch.object(LIFECYCLE, "stop_group", return_value=True), mock.patch.object(
                LIFECYCLE, "running_containers", return_value=set()
            ), mock.patch.object(LIFECYCLE.subprocess, "run") as run:
                LIFECYCLE.stop(args)

            gateway_call = run.call_args_list[0]
            self.assertEqual(
                [str(root / "scripts/stop_gateway_lan_lab.sh")], gateway_call.args[0]
            )
            self.assertEqual("1", gateway_call.kwargs["env"]["SISTER_COMPONENT_STOP_ONLY"])
            history = executions / "test-execution.json"
            payload = json.loads(history.read_text())
            self.assertEqual("STOPPED", payload["status"])
            self.assertEqual(["sister_reference"], payload["stopped_process_groups"])
            self.assertFalse(state.exists())


if __name__ == "__main__":
    unittest.main()
