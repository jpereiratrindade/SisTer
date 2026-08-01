#!/usr/bin/env python3
import http.client
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

from sisterd_nexo_identity_test import (
    PRIVATE_KEY,
    register,
    reserve_port,
    start_sisterd,
    stop_sisterd,
)


PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAzUnUCnCF15ZpU/SEX0AV1x2TEH/DaCbMYuChuIYyWik=
-----END PUBLIC KEY-----
"""


def start_nexo(executable, web_root, database_url, public_key, port):
    environment = os.environ.copy()
    environment.update(
        {
            "NEXO_HOST": "127.0.0.1",
            "NEXO_PORT": str(port),
            "NEXO_WEB_ROOT": str(web_root),
            "NEXO_DATABASE_URL": database_url,
            "NEXO_REQUIRE_SIGNED_INTERNAL_IDENTITY": "true",
            "NEXO_INTERNAL_IDENTITY_PUBLIC_KEYS": f"identity-2026-08={public_key}",
        }
    )
    process = subprocess.Popen(
        [str(executable), str(web_root)],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("Nexo exited before readiness: " + process.stderr.read())
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.3)
            connection.request("GET", "/api/health")
            response = connection.getresponse()
            response.read()
            connection.close()
            if response.status == 200:
                return process
        except OSError:
            time.sleep(0.05)
    raise AssertionError("Nexo did not become ready")


def stop(process):
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    return process.stderr.read()


def call_sisterd(port, cookie):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request(
        "GET",
        "/integrations/nexo/projects?limit=1",
        headers={
            "Cookie": f"unrelated=value; {cookie}",
            "Authorization": "Bearer externally-forged",
            "X-Sister-Subject": "forged-subject",
            "X-Sister-Role": "admin",
            "X-Request-ID": "externally-forged-request",
        },
    )
    response = connection.getresponse()
    payload = response.read()
    headers = {name.lower(): value for name, value in response.getheaders()}
    status = response.status
    connection.close()
    return status, headers, payload


def main():
    sisterd, sister_web, nexo, nexo_web, database_url = sys.argv[1:6]
    with tempfile.TemporaryDirectory(prefix="sec02v-e2e-") as temporary:
        root = Path(temporary)
        private_key = root / "identity-private.pem"
        public_key = root / "identity-public.pem"
        private_key.write_bytes(PRIVATE_KEY)
        public_key.write_text(PUBLIC_KEY)
        private_key.chmod(0o600)
        public_key.chmod(0o644)

        nexo_port = reserve_port()
        sister_port = reserve_port()
        nexo_process = start_nexo(nexo, nexo_web, database_url, public_key, nexo_port)
        sister_process = start_sisterd(
            sisterd,
            sister_web,
            sister_port,
            nexo_port,
            root / "auth.tsv",
            private_key,
        )
        try:
            cookie = register(sister_port, "sec02v-e2e@test.invalid")
            status, headers, payload = call_sisterd(sister_port, cookie)
            assert status == 200, (status, payload)
            assert headers.get("x-request-id"), "Nexo did not return the verified request_id"
            assert headers["x-request-id"] != "externally-forged-request"
            assert sister_process.poll() is None
            assert nexo_process.poll() is None
        finally:
            stop_sisterd(sister_process)
            nexo_logs = stop(nexo_process)

        sister_logs = sister_process.stderr.read()
        combined_logs = sister_logs + nexo_logs
        assert PRIVATE_KEY.decode() not in combined_logs
        assert "forged-cookie=value" not in combined_logs
        assert "Bearer externally-forged" not in combined_logs
        assert "sec02v-e2e@test.invalid" not in nexo_logs

    print("sec02v_sisterd_nexo_e2e ok")


if __name__ == "__main__":
    main()
