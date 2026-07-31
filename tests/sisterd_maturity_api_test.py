#!/usr/bin/env python3
import http.client
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def reserve_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def request(port, method, path, body=None, cookie=None):
    headers = {"Accept": "application/json"}
    if body is not None:
        body = json.dumps(body)
        headers["Content-Type"] = "application/json"
    if cookie:
        headers["Cookie"] = cookie
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    payload = response.read()
    result = (response.status, dict(response.getheaders()), payload)
    connection.close()
    return result


def session_cookie(headers):
    return headers["Set-Cookie"].split(";", 1)[0]


def wait_for_server(port, process):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("sisterd exited before accepting requests")
        try:
            if request(port, "GET", "/api/health")[0] == 200:
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("sisterd did not become ready")


def main():
    executable, web_root, source_root = sys.argv[1:4]
    port = reserve_port()
    with tempfile.TemporaryDirectory(prefix="sister-maturity-api-") as temporary:
        maturity_root = Path(temporary) / "maturity"
        environment = os.environ.copy()
        environment.update({
            "SISTER_ENV": "development",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_AUTH_FILE": str(Path(temporary) / "auth.tsv"),
            "SISTER_MATURITY_ROOT": str(maturity_root),
            "SISTER_DATABASE_URL": "",
            "SISTER_WORKERS": "4",
        })
        process = subprocess.Popen(
            [executable, str(port), web_root], env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        )
        try:
            wait_for_server(port, process)
            status, headers, _ = request(port, "POST", "/api/auth/register", {
                "name": "Maturity Admin", "email": "maturity-admin@test.invalid",
                "password": "maturity-admin-password",
            })
            assert status == 201, status
            admin_cookie = session_cookie(headers)
            status, headers, payload = request(port, "GET", "/api/me/capabilities", cookie=admin_cookie)
            assert status == 200, status
            capabilities = json.loads(payload)["capabilities"]
            assert "sister.maturity.read" in capabilities
            assert headers.get("Cache-Control") == "no-store", headers

            assert request(port, "GET", "/api/admin/maturity/latest")[0] == 401
            assert request(port, "GET", "/admin/maturity")[0] == 303
            assert request(port, "GET", "/api/admin/maturity/latest", cookie=admin_cookie)[0] == 404

            maturity_root.mkdir(parents=True)
            (maturity_root / "latest.json").write_text("{}\n", encoding="utf-8")
            assert request(port, "GET", "/api/admin/maturity/latest", cookie=admin_cookie)[0] == 503

            example = Path(source_root) / "contracts" / "maturity" / "1.0.0" / "example.json"
            (maturity_root / "latest.json").write_bytes(example.read_bytes())
            status, headers, payload = request(port, "GET", "/api/admin/maturity/latest", cookie=admin_cookie)
            assert status == 200, status
            assert headers.get("Cache-Control") == "no-store", headers
            assert json.loads(payload)["schema"] == "sister.maturity-status/1.0.0"
            assert request(port, "GET", "/api/admin/maturity/latest?path=/etc/passwd", cookie=admin_cookie)[0] == 200
            assert request(port, "POST", "/api/admin/maturity/latest", cookie=admin_cookie)[0] == 405

            status, _, _ = request(port, "POST", "/api/admin/users", {
                "name": "Maturity Reader", "email": "maturity-reader@test.invalid",
                "password": "maturity-reader-password", "role": "user",
            }, admin_cookie)
            assert status == 201, status
            status, headers, _ = request(port, "POST", "/api/auth/login", {
                "email": "maturity-reader@test.invalid", "password": "maturity-reader-password",
            })
            assert status == 200, status
            reader_cookie = session_cookie(headers)
            assert request(port, "GET", "/api/admin/maturity/latest", cookie=reader_cookie)[0] == 403

            assert request(port, "GET", "/api/admin/maturity/history", cookie=admin_cookie)[0] == 404
            history_root = maturity_root / "history"
            history_root.mkdir()
            (history_root / "index.json").write_text(
                '{"schema":"sister.maturity-history/1.0.0","items":[]}\n', encoding="utf-8"
            )
            assert request(port, "GET", "/api/admin/maturity/history", cookie=admin_cookie)[0] == 200
            assert request(port, "GET", "/api/admin/maturity/catalog", cookie=admin_cookie)[0] == 404
            (maturity_root / "catalog.json").write_text(
                '{"schema":"sister.maturity-catalog/1.0.0","generated_at":"2026-07-31T00:00:00Z","components":[]}\n',
                encoding="utf-8",
            )
            assert request(port, "GET", "/api/admin/maturity/catalog", cookie=admin_cookie)[0] == 200
            status, _, page = request(port, "GET", "/admin/maturity", cookie=admin_cookie)
            assert status == 200 and b"Centro de Engenharia do SisTer" in page
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    print("sisterd_maturity_api_tests ok")


if __name__ == "__main__":
    main()
