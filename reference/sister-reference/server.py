#!/usr/bin/env python3
"""Controlled implementation of the SisTer subsystem contract."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
from pathlib import Path
import random
import time


ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
HOST = "127.0.0.1"
PORT = integer_port = int(os.environ.get("SISTER_REFERENCE_PORT", "19001"))
if not 1024 <= integer_port <= 65535:
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
        if self.path in {"/api/health", "/_sister/health"}:
            if MODE == "unavailable":
                self.close_connection = True
                return
            status = "degraded" if MODE == "degraded" else "ok"
            self.response(200, {"status": status, "service": "sister-reference", "mode": MODE})
            return
        if self.path == "/_sister/ready":
            self.response(200 if MODE == "healthy" else 503, {"ready": MODE == "healthy"})
            return
        if self.path in {"/_sister/manifest", "/api/identity"}:
            self.response(200, MANIFEST)
            return
        if self.path == "/_sister/capabilities":
            self.response(200, {"capabilities": MANIFEST["capabilities"]})
            return
        if self.path == "/api/whoami":
            if not self.trusted():
                self.response(401, {"error": "trusted_proxy_required"})
                return
            if self.controlled_failure():
                return
            self.response(200, {
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
        if self.path != "/api/echo":
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
        self.response(200, {"value": payload["value"], "processed_by": "sister_reference"})


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    print(f"sister-reference listening on http://{HOST}:{PORT} mode={MODE}", flush=True)
    server.serve_forever()
