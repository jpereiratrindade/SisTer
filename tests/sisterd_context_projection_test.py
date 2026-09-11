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

PROJECTION = {
    "project": {
        "id": "PROJ-RESILIENCIA",
        "status": "active",
        "ref": {
            "authority": "sister_nexo",
            "kind": "research.project",
            "id": "PROJ-RESILIENCIA",
        },
    },
    "activity": {
        "id": "AP-PREVIEW-001",
        "title": "Mapeamento de vulnerabilidades ecológicas",
        "active": True,
        "ref": {
            "authority": "sister_nexo",
            "kind": "research.activity",
            "id": "AP-PREVIEW-001",
        },
    },
}


def reserve_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for_server(port, process):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("sisterd exited before readiness: " + process.stderr.read())
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


def start_sisterd(executable, web_root, port, auth_file, nexo_port, key_file, enabled=True):
    environment = os.environ.copy()
    environment.update(
        {
            "SISTER_ENV": "development",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_AUTH_FILE": str(auth_file),
            "SISTER_COOKIE_SECURE": "false",
            "SISTER_DATABASE_URL": "",
            "SISTER_ENABLE_LEGACY_PROXY": "false",
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "false",
            "SISTER_ENABLE_NEXO_CONTEXT_PROJECTION": "true" if enabled else "false",
        }
    )
    if enabled:
        environment.update(
            {
                "SISTER_NEXO_PORT": str(nexo_port),
                "SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE": str(key_file),
                "SISTER_INTERNAL_IDENTITY_KEY_ID": "identity-2026-08",
                "SISTER_INTERNAL_IDENTITY_TTL_SECONDS": "60",
            }
        )
    else:
        environment.pop("SISTER_NEXO_PORT", None)
        environment.pop("SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE", None)
        environment.pop("SISTER_INTERNAL_IDENTITY_KEY_ID", None)
        environment.pop("SISTER_INTERNAL_IDENTITY_TTL_SECONDS", None)

    process = subprocess.Popen(
        [executable, str(port), web_root],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    wait_for_server(port, process)
    return process


def stop_process(process):
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
        {
            "name": "Context Projection Test",
            "email": email,
            "password": "context-test-password-123",
        }
    )
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    connection.request(
        "POST",
        "/api/auth/register",
        body,
        {"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    payload = response.read()
    assert response.status == 201, (response.status, payload)
    cookie = response.getheader("Set-Cookie").split(";", 1)[0]
    connection.close()
    return cookie


def current_actor_id(port, cookie):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    connection.request("GET", "/api/me", headers={"Cookie": cookie})
    response = connection.getresponse()
    payload = response.read()
    assert response.status == 200, (response.status, payload)
    connection.close()
    return json.loads(payload)["id"]


def call_context(port, cookie=None, method="GET", query=""):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    target = "/api/v1/context-projection" + query
    headers = {
        "Authorization": "Bearer externally-forged",
        "X-Sister-Subject": "forged-subject",
        "X-Sister-Role": "admin",
        "X-Request-ID": "externally-forged-request",
        "Accept": "application/json",
    }
    if cookie is not None:
        headers["Cookie"] = f"unrelated=value; {cookie}"
    connection.request(
        method,
        target,
        headers=headers,
    )
    response = connection.getresponse()
    payload = response.read()
    status = response.status
    connection.close()
    return status, payload


def start_invalid_config_sisterd(executable, web_root, port, auth_file, environment_changes):
    environment = os.environ.copy()
    environment.update(
        {
            "SISTER_ENV": "development",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_AUTH_FILE": str(auth_file),
            "SISTER_COOKIE_SECURE": "false",
            "SISTER_DATABASE_URL": "",
            "SISTER_ENABLE_LEGACY_PROXY": "false",
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "false",
            "SISTER_ENABLE_NEXO_CONTEXT_PROJECTION": "true",
        }
    )
    for name in (
        "SISTER_NEXO_PORT",
        "SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE",
        "SISTER_INTERNAL_IDENTITY_KEY_ID",
        "SISTER_INTERNAL_IDENTITY_TTL_SECONDS",
    ):
        environment.pop(name, None)
    for name, value in environment_changes.items():
        if value is None:
            environment.pop(name, None)
        else:
            environment[name] = str(value)

    return subprocess.Popen(
        [executable, str(port), web_root],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )


def mock_nexo(port, captured, ready, expected_requests=2):
    payload = json.dumps(PROJECTION, separators=(",", ":")).encode()
    response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        + f"Content-Length: {len(payload)}\r\n".encode()
        + b"Connection: close\r\n\r\n"
        + payload
    )

    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
        listener.listen(expected_requests)
        listener.settimeout(4)
        ready.set()

        for _ in range(expected_requests):
            connection, _ = listener.accept()
            with connection:
                request = b""
                while b"\r\n\r\n" not in request:
                    chunk = connection.recv(8192)
                    if not chunk:
                        break
                    request += chunk
                captured.append(request.decode("iso-8859-1"))
                connection.sendall(response)


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


def assert_signed_request(raw, actor_id):
    request_line, headers = parse_headers(raw)
    assert request_line == "GET /api/v1/context-projection HTTP/1.1"
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
    protected = decode_segment(encoded_header)
    claims = decode_segment(encoded_claims)

    assert protected == {
        "alg": "EdDSA",
        "typ": "sister-internal+jwt",
        "kid": "identity-2026-08",
    }
    assert claims["iss"] == "sisterd"
    assert claims["sub"] == actor_id
    assert claims["aud"] == "sister_nexo"
    assert claims["capabilities"] == ["nexo.context.read"]
    assert claims["purpose"] == "research_operations"
    assert claims["request_id"] == headers["x-request-id"]
    assert claims["request_id"] != "externally-forged-request"
    assert len(claims["jti"]) == 32
    assert claims["exp"] - claims["iat"] == 60
    return assertion, claims


def main():
    executable, web_root = sys.argv[1:3]

    with tempfile.TemporaryDirectory(prefix="sister-context-projection-") as temporary:
        root = Path(temporary)
        key_file = root / "identity-private.pem"
        key_file.write_bytes(PRIVATE_KEY)
        key_file.chmod(0o600)

        nexo_port = reserve_port()
        captured = []
        ready = threading.Event()
        mock = threading.Thread(
            target=mock_nexo,
            args=(nexo_port, captured, ready, 2),
            daemon=True,
        )
        mock.start()
        assert ready.wait(timeout=2)

        sister_port = reserve_port()
        process = start_sisterd(
            executable,
            web_root,
            sister_port,
            root / "auth.tsv",
            nexo_port,
            key_file,
            enabled=True,
        )

        assertions = []
        try:
            status, _ = call_context(sister_port)
            assert status == 401, status
            assert not captured, "unauthenticated request must not open a Nexo connection"

            cookie = register(sister_port, "context@test.invalid")
            actor_id = current_actor_id(sister_port, cookie)

            for _ in range(2):
                status, payload = call_context(sister_port, cookie)
                assert status == 200, (status, payload)
                projection = json.loads(payload)
                assert projection == PROJECTION, projection
                assert projection["project"]["ref"] == {
                    "authority": "sister_nexo",
                    "kind": "research.project",
                    "id": "PROJ-RESILIENCIA",
                }
                assert projection["activity"]["ref"] == {
                    "authority": "sister_nexo",
                    "kind": "research.activity",
                    "id": "AP-PREVIEW-001",
                }

            mock.join(timeout=4)
            assert len(captured) == 2

            claims = []
            for raw in captured:
                assertion, decoded = assert_signed_request(raw, actor_id)
                assertions.append(assertion)
                claims.append(decoded)

            assert claims[0]["jti"] != claims[1]["jti"]
            assert claims[0]["request_id"] != claims[1]["request_id"]

            status, _ = call_context(sister_port, cookie, method="POST")
            assert status == 405, status
            assert len(captured) == 2, "invalid method must not open a Nexo connection"

            status, _ = call_context(sister_port, cookie, query="?forged=true")
            assert status == 400, status
            assert len(captured) == 2, "query must not open a Nexo connection"
        finally:
            stop_process(process)

        stderr = process.stderr.read()
        for assertion in assertions:
            assert assertion not in stderr
        assert PRIVATE_KEY.decode() not in stderr
        assert "Bearer externally-forged" not in stderr
        assert "context@test.invalid" not in stderr

        disabled_port = reserve_port()
        disabled_process = start_sisterd(
            executable,
            web_root,
            disabled_port,
            root / "disabled-auth.tsv",
            reserve_port(),
            key_file,
            enabled=False,
        )
        try:
            cookie = register(disabled_port, "disabled-context@test.invalid")
            status, _ = call_context(disabled_port, cookie)
            assert status == 404, status
        finally:
            stop_process(disabled_process)

        missing_port_process = start_invalid_config_sisterd(
            executable,
            web_root,
            reserve_port(),
            root / "missing-port-auth.tsv",
            {
                "SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE": key_file,
                "SISTER_INTERNAL_IDENTITY_KEY_ID": "identity-2026-08",
            },
        )
        assert missing_port_process.wait(timeout=5) != 0
        missing_port_stderr = missing_port_process.stderr.read()
        assert "SISTER_NEXO_PORT" in missing_port_stderr

        missing_key_process = start_invalid_config_sisterd(
            executable,
            web_root,
            reserve_port(),
            root / "missing-key-auth.tsv",
            {
                "SISTER_NEXO_PORT": reserve_port(),
                "SISTER_INTERNAL_IDENTITY_KEY_ID": "identity-2026-08",
            },
        )
        assert missing_key_process.wait(timeout=5) != 0
        missing_key_stderr = missing_key_process.stderr.read()
        assert "SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE" in missing_key_stderr

        relative_key_process = start_invalid_config_sisterd(
            executable,
            web_root,
            reserve_port(),
            root / "relative-key-auth.tsv",
            {
                "SISTER_NEXO_PORT": reserve_port(),
                "SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE": "relative-key.pem",
                "SISTER_INTERNAL_IDENTITY_KEY_ID": "identity-2026-08",
            },
        )
        assert relative_key_process.wait(timeout=5) != 0
        relative_key_stderr = relative_key_process.stderr.read()
        assert "must be absolute" in relative_key_stderr

    print("sisterd_context_projection_tests ok")


if __name__ == "__main__":
    main()
