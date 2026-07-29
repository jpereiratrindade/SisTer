#!/usr/bin/env python3
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import sys
import threading
import unittest


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


if __name__ == "__main__":
    unittest.main()
