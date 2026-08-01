#!/usr/bin/env python3
import http.client
import os
import socket
import subprocess
import sys
import tempfile
import time


def reserve_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def run_to_exit(executable, web_root, overrides):
    environment = os.environ.copy()
    environment.update(
        {
            "SISTER_ENV": "production",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_ENABLE_LEGACY_PROXY": "false",
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "false",
            "SISTER_DATABASE_URL": "",
        }
    )
    environment.update(overrides)
    with tempfile.TemporaryDirectory(prefix="sisterd-transport-test-") as temporary:
        environment["SISTER_AUTH_FILE"] = os.path.join(temporary, "auth.tsv")
        return subprocess.run(
            [executable, str(reserve_port()), web_root],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=False,
        )


def assert_rejected(executable, web_root, overrides, expected):
    result = run_to_exit(executable, web_root, overrides)
    assert result.returncode != 0, (overrides, result.stderr)
    assert expected in result.stderr, result.stderr


def assert_safe_production_starts(executable, web_root):
    port = reserve_port()
    environment = os.environ.copy()
    environment.update(
        {
            "SISTER_ENV": "production",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_ENABLE_LEGACY_PROXY": "false",
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "false",
            "SISTER_DATABASE_URL": "",
        }
    )
    with tempfile.TemporaryDirectory(prefix="sisterd-transport-test-") as temporary:
        environment["SISTER_AUTH_FILE"] = os.path.join(temporary, "auth.tsv")
        process = subprocess.Popen(
            [executable, str(port), web_root],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise AssertionError(process.stderr.read())
                try:
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.2)
                    connection.request("GET", "/api/health")
                    response = connection.getresponse()
                    response.read()
                    connection.close()
                    if response.status == 200:
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                raise AssertionError("safe production configuration did not start")

            for path in ("/integrations/clima/", "/integrations/nexo/"):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
                connection.request("GET", path)
                response = connection.getresponse()
                response.read()
                connection.close()
                assert response.status == 404, (path, response.status)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def main():
    executable, web_root = sys.argv[1:3]
    loopback_error = "production sisterd must bind to an IPv4 loopback address"
    assert_rejected(executable, web_root, {"SISTER_ENV": "developmnt"}, "invalid SISTER_ENV")
    assert_rejected(executable, web_root, {"SISTER_BIND_HOST": "0.0.0.0"}, loopback_error)
    assert_rejected(executable, web_root, {"SISTER_BIND_HOST": "192.0.2.10"}, loopback_error)
    assert_rejected(
        executable,
        web_root,
        {"SISTER_ENABLE_LEGACY_PROXY": "true"},
        "legacy HTTP proxy is forbidden in production",
    )
    assert_rejected(
        executable,
        web_root,
        {"SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "true"},
        "legacy WebSocket proxy is forbidden in production",
    )
    assert_safe_production_starts(executable, web_root)
    print("sisterd_transport_quarantine_tests ok")


if __name__ == "__main__":
    main()
