#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile


def run_to_exit(executable, web_root, overrides):
    environment = os.environ.copy()
    environment.update(
        {
            "SISTER_ENV": "production",
            "SISTER_LISTENER_MODE": "systemd-unix",
            "SISTER_ACTIVATED_SOCKET_PATH": "/run/sister/sisterd.sock",
            "SISTER_WEB_ROOT": web_root,
            "SISTER_ENABLE_HTTP_BOOTSTRAP": "false",
            "SISTER_ENABLE_LEGACY_PROXY": "false",
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "false",
            "SISTER_DATABASE_URL": "",
        }
    )
    environment.update(overrides)
    with tempfile.TemporaryDirectory(prefix="sisterd-transport-test-") as temporary:
        environment["SISTER_AUTH_FILE"] = os.path.join(temporary, "auth.tsv")
        return subprocess.run(
            [executable],
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


def main():
    executable, web_root = sys.argv[1:3]
    assert_rejected(executable, web_root, {"SISTER_ENV": "developmnt"}, "invalid SISTER_ENV")
    assert_rejected(
        executable,
        web_root,
        {"SISTER_ENABLE_HTTP_BOOTSTRAP": "true"},
        "HTTP administrator bootstrap is forbidden in production",
    )
    assert_rejected(
        executable, web_root, {"SISTER_BIND_HOST": "127.0.0.1"},
        "production TCP listener configuration is forbidden")
    assert_rejected(
        executable, web_root, {"SISTER_PORT": "8000"},
        "production TCP listener configuration is forbidden")
    assert_rejected(
        executable, web_root, {"SISTER_LISTENER_MODE": "tcp-loopback"},
        "requires the systemd-activated Unix listener")
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
    assert_rejected(
        executable, web_root, {},
        "missing socket activation variable")
    print("sisterd_transport_quarantine_tests ok")


if __name__ == "__main__":
    main()
