#!/usr/bin/env python3
"""Controlled implementation of the SisTer subsystem contract."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import random
import time


ROOT = Path(__file__).resolve().parent
MANIFEST_BYTES = (ROOT / "manifest.json").read_bytes()
MANIFEST = json.loads(MANIFEST_BYTES)
MANIFEST_DIGEST = "sha256:" + hashlib.sha256(MANIFEST_BYTES).hexdigest()
HOST = "127.0.0.1"
PORT = int(os.environ.get("SISTER_REFERENCE_PORT", "19001"))
if not 1024 <= PORT <= 65535:
    raise SystemExit("invalid SISTER_REFERENCE_PORT")
MODES = {
    "healthy", "degraded", "unavailable", "delayed", "invalid-response",
    "http-401", "http-403", "http-404", "http-500", "connection-closed",
}


def integer_environment(name: str, default: int, minimum: int, maximum: int) -> int:
    value = int(os.environ.get(name, str(default)))
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} outside allowed range")
    return value


MODE = os.environ.get("SISTER_REFERENCE_MODE", "healthy")
if MODE not in MODES:
    raise SystemExit(f"invalid SISTER_REFERENCE_MODE: {MODE}")
DELAY_MS = integer_environment("SISTER_REFERENCE_DELAY_MS", 0, 0, 120_000)
FAILURE_RATE = integer_environment("SISTER_REFERENCE_FAILURE_RATE", 0, 0, 100)
PROXY_TOKEN = os.environ.get("SISTER_INTERNAL_PROXY_TOKEN", "")
if len(PROXY_TOKEN) < 32:
    raise SystemExit("SISTER_INTERNAL_PROXY_TOKEN must contain at least 32 characters")


class Handler(BaseHTTPRequestHandler):
    server_version = "sister-reference/0.1.0"
    sys_version = ""

    def log_message(self, format_string: str, *args: object) -> None:
        print(f"reference peer={self.client_address[0]} " + format_string % args, flush=True)

    def response(self, status: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def trusted(self) -> bool:
        supplied = self.headers.get("X-Sister-Proxy-Token", "")
        return hmac.compare_digest(supplied, PROXY_TOKEN)

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def controlled_failure(self) -> bool:
        if DELAY_MS or MODE == "delayed":
            time.sleep(max(DELAY_MS, 1_000 if MODE == "delayed" else 0) / 1000)
        if MODE == "connection-closed":
            self.close_connection = True
            return True
        if MODE == "invalid-response":
            self.connection.sendall(b"not-http")
            self.close_connection = True
            return True
        statuses = {"http-401": 401, "http-403": 403, "http-404": 404, "http-500": 500}
        if MODE in statuses or (FAILURE_RATE and random.SystemRandom().randrange(100) < FAILURE_RATE):
            self.response(statuses.get(MODE, 500), {"error": "controlled_failure", "mode": MODE})
            return True
        return False

    def do_GET(self) -> None:
        if self.path in {"/health", "/api/health", "/_sister/health"}:
            if MODE == "unavailable":
                self.close_connection = True
                return
            status = "degraded" if MODE == "degraded" else "ok"
            self.response(200, {
                "schema": "sister.subsystem.health/1.0.0",
                "system_id": "sister_reference",
                "status": status,
                "checked_at": self.now(),
            })
            return
        if self.path in {"/ready", "/_sister/ready"}:
            ready = MODE == "healthy"
            self.response(200 if ready else 503, {
                "schema": "sister.subsystem.readiness/1.0.0",
                "system_id": "sister_reference",
                "status": "ready" if ready else "not_ready",
                "contract_version": "1.0.0",
                "manifest_digest": MANIFEST_DIGEST,
                "dependencies": {},
                "degraded_capabilities": [],
            })
            return
        if self.path in {"/manifest", "/_sister/manifest", "/api/identity"}:
            self.response(200, MANIFEST)
            return
        if self.path in {"/capabilities", "/_sister/capabilities"}:
            self.response(200, {
                "schema": "sister.subsystem.capabilities/1.0.0",
                "contract": MANIFEST["contract"],
                "system_id": MANIFEST["system_id"],
                "generated_at": self.now(),
                "capabilities": [
                    {"id": "reference.identity.read", "description": "Read mediated identity", "risk": "low"},
                    {
                        "id": "reference.echo.execute",
                        "description": "Execute controlled echo through SisTer mediation",
                        "risk": "low",
                        "input_schema": "sister.echo.request/1.0.0",
                        "output_schema": "sister.subsystem.echo/1.0.0",
                        "observable_success": "response.value equals request.value and response.processed_by equals sister_reference",
                    },
                ],
            })
            return
        if self.path in {"/identity", "/api/whoami"}:
            if not self.trusted():
                self.response(401, {"error": "trusted_proxy_required"})
                return
            if self.controlled_failure():
                return
            self.response(200, {
                "schema": "sister.subsystem.identity/1.0.0",
                "subject": self.headers.get("X-Sister-Subject"),
                "name": self.headers.get("X-Sister-Name"),
                "email": self.headers.get("X-Sister-Email"),
                "role": self.headers.get("X-Sister-Role"),
                "request_id": self.headers.get("X-Request-ID"),
                "origin": "sisterd",
            })
            return
        self.response(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path not in {"/echo", "/api/echo"}:
            self.response(404, {"error": "not_found"})
            return
        if not self.trusted():
            self.response(401, {"error": "trusted_proxy_required"})
            return
        if self.controlled_failure():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65_536:
                raise ValueError
            payload = json.loads(self.rfile.read(length))
            if set(payload) != {"value"} or not isinstance(payload["value"], str):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            self.response(400, {"error": "invalid_echo_payload"})
            return
        self.response(200, {
            "schema": "sister.subsystem.echo/1.0.0",
            "value": payload["value"],
            "processed_by": "sister_reference",
        })


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    print(f"sister-reference listening on http://{HOST}:{PORT} mode={MODE}", flush=True)
    server.serve_forever()
