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
import threading
import time


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
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    payload = response.read()
    result = response.status, dict(response.getheaders()), payload
    connection.close()
    return result


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


def run_health_server(port, stop, ready, requests):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
        listener.listen(4)
        listener.settimeout(0.2)
        ready.set()
        while not stop.is_set():
            try:
                connection, _ = listener.accept()
            except socket.timeout:
                continue
            with connection:
                raw = b""
                while b"\r\n\r\n" not in raw:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    raw += chunk
                requests.append(raw.decode("iso-8859-1"))
                body = b'{"service":"sister-nexo","status":"ok"}'
                connection.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: application/json\r\n"
                    + f"Content-Length: {len(body)}\r\n".encode("ascii")
                    + b"Connection: close\r\n\r\n"
                    + body
                )


def find_nexo(payload):
    systems = json.loads(payload)
    return next(system for system in systems if system["id"] == "sister_nexo")


def main():
    executable, web_root = sys.argv[1:3]
    sister_port = reserve_port()
    nexo_port = reserve_port()
    stop = threading.Event()
    ready = threading.Event()
    observed_requests = []
    mock = threading.Thread(
        target=run_health_server,
        args=(nexo_port, stop, ready, observed_requests),
        daemon=True,
    )
    mock.start()
    assert ready.wait(timeout=2)

    with tempfile.TemporaryDirectory(prefix="sister-system-health-") as temporary:
        environment = os.environ.copy()
        environment.update({
            "SISTER_ENV": "development",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_AUTH_FILE": str(Path(temporary) / "auth.tsv"),
            "SISTER_DATABASE_URL": "",
            "SISTER_COOKIE_SECURE": "false",
            "SISTER_NEXO_PUBLIC_URL": "https://nexo-gateway.test:8443",
            "SISTER_NEXO_PORT": str(nexo_port),
            "SISTER_SUBSYSTEM_HEALTH_TIMEOUT_MS": "300",
        })
        process = subprocess.Popen(
            [executable, str(sister_port), web_root],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            wait_for_server(sister_port, process)
            status, headers, payload = request(sister_port, "POST", "/api/auth/register", {
                "name": "System Health Admin",
                "email": "system-health@test.invalid",
                "password": "system-health-password",
            })
            assert status == 201, (status, payload)
            cookie = headers["Set-Cookie"].split(";", 1)[0]

            status, _, payload = request(sister_port, "GET", "/api/systems", cookie=cookie)
            assert status == 200, (status, payload)
            nexo = find_nexo(payload)
            assert nexo["health_status"] == "online", nexo
            assert nexo["health_observed_by"] == "sisterd", nexo
            assert nexo["health_http_status"] == 200, nexo
            assert nexo["health_detail"] == "ok", nexo
            assert "health_url" not in nexo, nexo
            assert observed_requests and observed_requests[-1].startswith(
                "GET /api/health HTTP/1.1\r\n"
            ), observed_requests

            stop.set()
            mock.join(timeout=2)
            assert not mock.is_alive()

            status, _, payload = request(sister_port, "GET", "/api/systems", cookie=cookie)
            assert status == 200, (status, payload)
            nexo = find_nexo(payload)
            assert nexo["health_status"] == "offline", nexo
            assert nexo["health_observed_by"] == "sisterd", nexo
            assert nexo["health_http_status"] == 0, nexo
        finally:
            stop.set()
            mock.join(timeout=1)
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

    app_js = (Path(web_root) / "app.js").read_text(encoding="utf-8")
    assert "checkSystemHealth" not in app_js
    assert 'mode: "cors"' not in app_js
    assert "system.health_url" not in app_js
    print("sisterd_system_catalog_health_tests ok")


if __name__ == "__main__":
    main()
