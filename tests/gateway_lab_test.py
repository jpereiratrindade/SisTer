#!/usr/bin/env python3
import http.client
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

from gateway_lab_support import haproxy_binary, request, running_haproxy, skip_or_fail, status


def wait_for_sisterd(process):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(process.stderr.read())
        try:
            connection = http.client.HTTPConnection("127.0.0.1", 8000, timeout=0.2)
            connection.request("GET", "/api/health")
            response = connection.getresponse()
            response.read()
            connection.close()
            if response.status == 200:
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("sisterd did not become ready on loopback:8000")


def stop(process):
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main():
    haproxy_binary()
    executable, web_root = sys.argv[1:3]
    with tempfile.TemporaryDirectory(prefix="sister-gateway-lab-") as temporary:
        environment = os.environ.copy()
        environment.update(
            {
                "SISTER_ENV": "production",
                "SISTER_BIND_HOST": "127.0.0.1",
                "SISTER_AUTH_FILE": str(Path(temporary) / "auth.tsv"),
                "SISTER_DATABASE_URL": "",
                "SISTER_ENABLE_HTTP_BOOTSTRAP": "false",
                "SISTER_ENABLE_LEGACY_PROXY": "false",
                "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "false",
                "SISTER_ENABLE_NEXO_SIGNED_INTEGRATION": "false",
            }
        )
        process = subprocess.Popen(
            [executable, "8000", web_root],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            wait_for_sisterd(process)
            with running_haproxy(expect_backend=True):
                assert status(request(path="/api/health")) == 200
                assert status(request(path="/integrations/clima/forecast")) == 404
                nexo_status = status(request(path="/integrations/nexo/projects"))
                assert nexo_status in (401, 403, 404), nexo_status
        finally:
            stop(process)
    print("gateway_lab_tests ok")


if __name__ == "__main__":
    skip_or_fail(main)
