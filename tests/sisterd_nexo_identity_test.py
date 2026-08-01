#!/usr/bin/env python3
import base64
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


PRIVATE_KEY = b"""-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIIUfIgspmWAUj39fzrFNyE12Q4sfpRfjS3NiIiVC/LOn
-----END PRIVATE KEY-----
"""


def reserve_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for_server(port, process):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("sisterd exited before accepting requests")
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.2)
            connection.request("GET", "/api/health")
            response = connection.getresponse()
            response.read()
            connection.close()
            if response.status == 200:
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("sisterd did not become ready")


def start_sisterd(executable, web_root, port, nexo_port, auth_file, key_file=None):
    environment = os.environ.copy()
    environment.update(
        {
            "SISTER_ENV": "development",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_AUTH_FILE": str(auth_file),
            "SISTER_NEXO_PORT": str(nexo_port),
            "SISTER_COOKIE_SECURE": "false",
            "SISTER_DATABASE_URL": "",
            "SISTER_ENABLE_LEGACY_PROXY": "true",
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "false",
            "SISTER_INTERNAL_IDENTITY_KEY_ID": "identity-2026-08",
            "SISTER_INTERNAL_IDENTITY_TTL_SECONDS": "60",
        }
    )
    environment.pop("SISTER_INTERNAL_PROXY_TOKEN", None)
    environment.pop("SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE", None)
    if key_file is not None:
        environment["SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE"] = str(key_file)
    process = subprocess.Popen(
        [executable, str(port), web_root],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    wait_for_server(port, process)
    return process


def stop_sisterd(process):
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def register(port, email):
    body = json.dumps(
        {"name": "Nexo Identity Test", "email": email, "password": "nexo-test-password-123"}
    )
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    connection.request("POST", "/api/auth/register", body, {"Content-Type": "application/json"})
    response = connection.getresponse()
    payload = response.read()
    assert response.status == 201, (response.status, payload)
    cookie = response.getheader("Set-Cookie").split(";", 1)[0]
    connection.close()
    return cookie


def call_nexo(port, cookie):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    connection.request(
        "GET",
        "/integrations/nexo/projects?limit=1",
        headers={
            "Cookie": f"unrelated=value; {cookie}",
            "Authorization": "Bearer externally-forged",
            "X-Sister-Subject": "forged-subject",
            "X-Sister-Role": "admin",
            "X-Request-ID": "externally-forged-request",
            "Accept": "application/json",
        },
    )
    response = connection.getresponse()
    payload = response.read()
    status = response.status
    connection.close()
    return status, payload


def run_mock_nexo(port, captured, ready):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
        listener.listen(1)
        listener.settimeout(3)
        ready.set()
        try:
            connection, _ = listener.accept()
        except socket.timeout:
            return
        with connection:
            request = b""
            while b"\r\n\r\n" not in request:
                chunk = connection.recv(8192)
                if not chunk:
                    break
                request += chunk
            captured.append(request.decode("iso-8859-1"))
            connection.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                b"Content-Length: 11\r\nConnection: close\r\n\r\n{\"ok\":true}"
            )


def parse_headers(raw):
    lines = raw.split("\r\n")
    headers = {}
    for line in lines[1:]:
        if not line:
            break
        name, value = line.split(":", 1)
        headers[name.lower()] = value.strip()
    return lines[0], headers


def decode_segment(value):
    return json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))


def main():
    executable, web_root = sys.argv[1:3]
    with tempfile.TemporaryDirectory(prefix="sister-nexo-identity-test-") as temporary:
        temporary_path = Path(temporary)
        key_file = temporary_path / "identity-private.pem"
        key_file.write_bytes(PRIVATE_KEY)
        key_file.chmod(0o600)

        sister_port = reserve_port()
        nexo_port = reserve_port()
        captured = []
        ready = threading.Event()
        mock = threading.Thread(
            target=run_mock_nexo, args=(nexo_port, captured, ready), daemon=True
        )
        mock.start()
        assert ready.wait(timeout=2)
        process = start_sisterd(
            executable,
            web_root,
            sister_port,
            nexo_port,
            temporary_path / "auth.tsv",
            key_file,
        )
        try:
            cookie = register(sister_port, "nexo-identity@test.invalid")
            status, payload = call_nexo(sister_port, cookie)
            assert status == 200, (status, payload)
            mock.join(timeout=3)
            assert len(captured) == 1, "Nexo did not receive the authorized request"
            request_line, headers = parse_headers(captured[0])
            assert request_line == "GET /projects?limit=1 HTTP/1.1"
            assert "cookie" not in headers
            assert "x-sister-subject" not in headers
            assert "x-sister-name" not in headers
            assert "x-sister-email" not in headers
            assert "x-sister-role" not in headers
            assert "x-sister-proxy-token" not in headers
            scheme, assertion = headers["authorization"].split(" ", 1)
            assert scheme == "Sister-Assertion"
            encoded_header, encoded_claims, signature = assertion.split(".")
            assert len(signature) >= 80
            assertion_header = decode_segment(encoded_header)
            claims = decode_segment(encoded_claims)
            assert assertion_header == {
                "alg": "EdDSA",
                "typ": "sister-internal+jwt",
                "kid": "identity-2026-08",
            }
            assert claims["iss"] == "sisterd"
            assert claims["aud"] == "sister_nexo"
            assert claims["capabilities"] == ["nexo.projects.read"]
            assert claims["purpose"] == "research_operations"
            assert claims["request_id"] == headers["x-request-id"]
            assert claims["exp"] - claims["iat"] == 60
            assert "nexo-identity@test.invalid" not in captured[0]
        finally:
            stop_sisterd(process)

        missing_key_port = reserve_port()
        unused_nexo_port = reserve_port()
        unexpected = []
        missing_ready = threading.Event()
        missing_mock = threading.Thread(
            target=run_mock_nexo,
            args=(unused_nexo_port, unexpected, missing_ready),
            daemon=True,
        )
        missing_mock.start()
        assert missing_ready.wait(timeout=2)
        process = start_sisterd(
            executable,
            web_root,
            missing_key_port,
            unused_nexo_port,
            temporary_path / "missing-auth.tsv",
        )
        try:
            cookie = register(missing_key_port, "missing-key@test.invalid")
            status, _ = call_nexo(missing_key_port, cookie)
            assert status == 502
            time.sleep(0.2)
            assert not unexpected, "key configuration failure must prevent the upstream request"
        finally:
            stop_sisterd(process)

    print("sisterd_nexo_identity_tests ok")


if __name__ == "__main__":
    main()
