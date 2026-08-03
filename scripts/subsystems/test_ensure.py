#!/usr/bin/env python3
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("ensure.py")
SPEC = importlib.util.spec_from_file_location("sister_subsystems_ensure", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
ENSURE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ENSURE
SPEC.loader.exec_module(ENSURE)


class HealthHandler(BaseHTTPRequestHandler):
    status = 200
    payload = b'{"status":"ok","service":"sister-nexo"}'

    def do_GET(self) -> None:
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.payload)

    def log_message(self, _format: str, *_args: object) -> None:
        return


class HealthResultTests(unittest.TestCase):
    def setUp(self) -> None:
        HealthHandler.status = 200
        HealthHandler.payload = json.dumps(
            {"status": "ok", "service": "sister-nexo"}
        ).encode()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def project(self, port: int) -> dict:
        return {
            "orchestration": {
                "health": {
                    "url": f"http://127.0.0.1:{port}/api/health",
                    "expected_json": {"status": "ok", "service": "sister-nexo"},
                }
            }
        }

    def test_confirms_expected_service(self) -> None:
        result = ENSURE.health_result(self.project(self.server.server_port))
        self.assertEqual("healthy", result.state)

    def test_rejects_wrong_service_on_occupied_port(self) -> None:
        HealthHandler.payload = b'{"status":"ok","service":"outro"}'
        result = ENSURE.health_result(self.project(self.server.server_port))
        self.assertEqual("occupied", result.state)

    def test_distinguishes_unavailable_port(self) -> None:
        with socket.socket() as candidate:
            candidate.bind(("127.0.0.1", 0))
            port = candidate.getsockname()[1]
        result = ENSURE.health_result(self.project(port))
        self.assertEqual("unavailable", result.state)


class SubsystemReportTests(unittest.TestCase):
    def result(self, component: str, required: bool, status: str) -> dict:
        return {
            "component": component,
            "required": required,
            "status": status,
            "phase": "health",
            "exit_code": None,
            "elapsed_seconds": 0.1,
            "log": None,
            "started_by_run": False,
            "detail": "test",
        }

    def test_optional_failure_is_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "subsystems.json"
            state = ENSURE.write_report(
                report,
                "dev",
                [self.result("optional", False, "DEGRADED")],
            )
            self.assertEqual("DEGRADED", state)
            self.assertEqual("DEGRADED", json.loads(report.read_text())["result"])

    def test_required_failure_is_blocked(self) -> None:
        state = ENSURE.write_report(
            None,
            "dev",
            [self.result("required", True, "DEGRADED")],
        )
        self.assertEqual("BLOCKED", state)

    def test_healthy_selection_is_ready(self) -> None:
        state = ENSURE.write_report(
            None,
            "dev",
            [self.result("ready", True, "READY")],
        )
        self.assertEqual("READY", state)


class RepositoryPathTests(unittest.TestCase):
    def test_resolves_repository_from_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = workspace / "cpp" / "sister-nexo"
            repository.mkdir(parents=True)
            with mock.patch.dict("os.environ", {"SISTER_WORKSPACE_ROOT": str(workspace)}, clear=False):
                resolved = ENSURE.repository_path(
                    {"id": "sister_nexo", "repository": "cpp/sister-nexo"}
                )
            self.assertEqual(repository.resolve(), resolved)

    def test_project_override_wins_over_workspace_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "custom-nexo"
            repository.mkdir()
            with mock.patch.dict(
                "os.environ",
                {"SISTER_REPOSITORY_ROOT_SISTER_NEXO": str(repository)},
                clear=False,
            ):
                resolved = ENSURE.repository_path(
                    {"id": "sister_nexo", "repository": "cpp/sister-nexo"}
                )
            self.assertEqual(repository.resolve(), resolved)

    def test_discovers_repository_by_integration_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            repository = workspace / "python" / "NexoLocal"
            repository.mkdir(parents=True)
            (repository / "SISTER_INTEGRATION.md").write_text(
                "Identificador no registro: `sister_nexo`.\n",
                encoding="utf-8",
            )
            with mock.patch.dict("os.environ", {"SISTER_WORKSPACE_ROOT": str(workspace)}, clear=False):
                resolved = ENSURE.repository_path(
                    {"id": "sister_nexo", "repository": "cpp/sister-nexo"}
                )
            self.assertEqual(repository.resolve(), resolved)

    def test_missing_repository_message_requests_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict("os.environ", {"SISTER_WORKSPACE_ROOT": temporary}, clear=False):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "SISTER_REPOSITORY_ROOT_SISTER_NEXO=/caminho/do/repositorio",
                ):
                    ENSURE.repository_path(
                        {"id": "sister_nexo", "repository": "cpp/sister-nexo"}
                    )


if __name__ == "__main__":
    unittest.main()
