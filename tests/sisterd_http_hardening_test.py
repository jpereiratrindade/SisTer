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


def reserve_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for_server(port, process, server_log):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            server_log.seek(0)
            raise AssertionError(server_log.read())
        try:
            assert_health(port)
            return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("sisterd did not become ready")


def assert_health(port):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    connection.request("GET", "/api/health")
    response = connection.getresponse()
    payload = response.read()
    connection.close()
    assert response.status == 200, (response.status, payload)


def raw_request(port, raw, source_ip="127.0.0.1", shutdown_write=False):
    with socket.socket() as connection:
        connection.settimeout(3)
        connection.bind((source_ip, 0))
        connection.connect(("127.0.0.1", port))
        connection.sendall(raw)
        if shutdown_write:
            connection.shutdown(socket.SHUT_WR)
        response = b""
        while True:
            chunk = connection.recv(8192)
            if not chunk:
                break
            response += chunk
    status_line = response.split(b"\r\n", 1)[0]
    assert status_line.startswith(b"HTTP/1.1 "), response
    return int(status_line.split()[1]), response


def login_response(port, email, source_ip="127.0.0.1"):
    body = json.dumps({"email": email, "password": "always-invalid-password"}).encode()
    request = (
        b"POST /api/auth/login HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Content-Type: application/json\r\n"
        + f"Content-Length: {len(body)}\r\n".encode()
        + b"Connection: close\r\n\r\n"
        + body
    )
    return raw_request(port, request, source_ip)


def login(port, email, source_ip="127.0.0.1"):
    return login_response(port, email, source_ip)[0]


def main():
    executable, web_root = sys.argv[1:3]
    port = reserve_port()
    environment = os.environ.copy()
    environment.update(
        {
            "SISTER_ENV": "development",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_COOKIE_SECURE": "false",
            "SISTER_ENABLE_HTTP_BOOTSTRAP": "false",
            "SISTER_ENABLE_LEGACY_PROXY": "false",
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "false",
            "SISTER_DATABASE_URL": "",
            "SISTER_WORKERS": "8",
            "SISTER_CLIENT_TIMEOUT_SECONDS": "2",
        }
    )
    with tempfile.TemporaryDirectory(prefix="sister-http-hardening-") as temporary, \
            tempfile.TemporaryFile(mode="w+") as server_log:
        environment["SISTER_AUTH_FILE"] = os.path.join(temporary, "auth.tsv")
        process = subprocess.Popen(
            [executable, str(port), web_root],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=server_log,
            text=True,
        )
        try:
            wait_for_server(port, process, server_log)
            hostile = [
                (b"Content-Length: abc\r\n", 400),
                (b"Content-Length: -1\r\n", 400),
                (b"Content-Length: +10\r\n", 400),
                (b"Content-Length:\r\n", 400),
                (b"Content-Length: 999999999999999999999\r\n", 413),
                (b"Content-Length: 16777217\r\n", 413),
                (b"Content-Length: 1 0\r\n", 400),
                (b"Content-Length: 1\r\nContent-Length: 1\r\n", 400),
            ]
            for header, expected in hostile:
                status, response = raw_request(
                    port,
                    b"POST /api/auth/login HTTP/1.1\r\nHost: localhost\r\n" +
                    header + b"Connection: close\r\n\r\n",
                )
                assert status == expected, (header, status, response)
                assert b"invalid Content-Length" not in response
                assert process.poll() is None
                assert_health(port)

            status, _ = raw_request(
                port,
                b"POST /api/auth/login HTTP/1.1\r\nHost: localhost\r\n"
                b"Content-Length: 16777216\r\nConnection: close\r\n\r\n",
                shutdown_write=True,
            )
            assert status == 400
            assert_health(port)

            for index in range(8):
                email = "Victim@Example.org" if index % 2 == 0 else "victim@example.org"
                assert login(port, email) == 401
            status, response = login_response(port, "victim@example.org")
            assert status == 429, (status, response)
            assert b"Retry-After:" in response
            assert_health(port)

            for index in range(24):
                assert login(port, f"changing-{index}@example.org") == 401
            assert login(port, "changing-blocked@example.org") == 429
            assert_health(port)

            for index in range(16):
                assert login(port, "cross-address@example.org", f"127.0.1.{index + 1}") == 401
            assert login(port, "cross-address@example.org", "127.0.2.1") == 429
            assert process.poll() is None
            assert_health(port)
        finally:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    print("sisterd_http_hardening_tests ok")


if __name__ == "__main__":
    main()
