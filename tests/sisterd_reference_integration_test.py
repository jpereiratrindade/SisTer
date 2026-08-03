#!/usr/bin/env python3
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference" / "sister-reference" / "server.py"


def reserve_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def request(port, method, path, body=None, cookie=None, headers=None):
    request_headers = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        body = json.dumps(body)
        request_headers["Content-Type"] = "application/json"
    if cookie:
        request_headers["Cookie"] = cookie
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    connection.request(method, path, body=body, headers=request_headers)
    response = connection.getresponse()
    payload = response.read()
    result = response.status, dict(response.getheaders()), payload
    connection.close()
    return result


def wait_for(port, process, path="/api/health"):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("process exited before readiness")
        try:
            if request(port, "GET", path)[0] == 200:
                return
        except OSError:
            pass
        time.sleep(0.05)
    raise AssertionError("process did not become ready")


def stop(process):
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def main():
    executable, web_root = sys.argv[1:3]
    sister_port = reserve_port()
    reference_port = reserve_port()
    token = "reference-test-token-" + "x" * 48
    reference_environment = os.environ.copy()
    reference_environment.update({
        "SISTER_REFERENCE_PORT": str(reference_port),
        "SISTER_REFERENCE_MODE": "healthy",
        "SISTER_INTERNAL_PROXY_TOKEN": token,
        "SISTER_HOME": str(ROOT),
    })
    reference = subprocess.Popen(
        [sys.executable, str(REFERENCE)], env=reference_environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    wait_for(reference_port, reference, "/health")
    for path in ("/manifest", "/health", "/ready", "/capabilities"):
        assert request(reference_port, "GET", path)[0] == 200, path
    assert request(reference_port, "GET", "/identity")[0] == 401
    assert request(reference_port, "POST", "/echo", {"value": "direct"})[0] == 401

    with tempfile.TemporaryDirectory(prefix="sister-reference-e2e-") as temporary:
        environment = os.environ.copy()
        environment.update({
            "SISTER_ENV": "development",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_AUTH_FILE": str(Path(temporary) / "auth.tsv"),
            "SISTER_DATABASE_URL": "",
            "SISTER_COOKIE_SECURE": "false",
            "SISTER_ENABLE_REFERENCE_SUBSYSTEM": "true",
            "SISTER_REFERENCE_PORT": str(reference_port),
            "SISTER_INTERNAL_PROXY_TOKEN": token,
        })
        sisterd = subprocess.Popen(
            [executable, str(sister_port), web_root], env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        )
        try:
            wait_for(sister_port, sisterd)
            status, headers, _ = request(sister_port, "POST", "/api/auth/register", {
                "name": "Reference Admin", "email": "reference@test.invalid",
                "password": "reference-test-password",
            })
            assert status == 201, status
            cookie = headers["Set-Cookie"].split(";", 1)[0]

            status, _, payload = request(
                sister_port, "GET", "/integrations/reference/identity", cookie=cookie,
                headers={"X-Sister-Subject": "forged", "X-Sister-Role": "admin"},
            )
            assert status == 200, (status, payload)
            identity = json.loads(payload)
            assert identity["subject"] != "forged", identity
            assert identity["role"] == "admin", identity
            assert identity["origin"] == "sisterd", identity

            status, _, payload = request(
                sister_port, "POST", "/integrations/reference/echo",
                {"value": "teste"}, cookie,
            )
            assert status == 200, (status, payload)
            assert json.loads(payload) == {
                "schema": "sister.subsystem.echo/1.0.0",
                "value": "teste",
                "processed_by": "sister_reference",
            }

            for path in ("manifest", "health", "ready", "capabilities"):
                status, _, _ = request(
                    sister_port, "GET", f"/integrations/reference/{path}", cookie=cookie)
                assert status == 200, path

            stop(reference)
            assert request(sister_port, "GET", "/integrations/reference/identity", cookie=cookie)[0] == 502
            assert request(sister_port, "GET", "/api/health")[0] == 200
        finally:
            stop(sisterd)
            stop(reference)
    print("sisterd_reference_integration_tests ok")


if __name__ == "__main__":
    main()
