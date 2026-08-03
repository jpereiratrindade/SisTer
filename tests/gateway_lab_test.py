#!/usr/bin/env python3
import sys
import tempfile

from gateway_lab_support import (
    UPSTREAM_SOCKET,
    haproxy_binary,
    request,
    running_haproxy,
    skip_or_fail,
    status,
)
from sisterd_unix_listener_test import create_listener, environment, start, stop, wait_for_health


def main():
    haproxy_binary()
    executable, web_root = sys.argv[1:3]
    try:
        UPSTREAM_SOCKET.unlink()
    except FileNotFoundError:
        pass
    with tempfile.TemporaryDirectory(prefix="sister-gateway-lab-") as temporary:
        listener = create_listener(UPSTREAM_SOCKET)
        sister_environment = environment(
            web_root, f"{temporary}/auth.tsv", UPSTREAM_SOCKET)
        process = start(executable, [listener.fileno()], sister_environment)
        try:
            wait_for_health(process, UPSTREAM_SOCKET)
            with running_haproxy(expect_backend=True):
                assert status(request(path="/api/health")) == 200
                assert status(request(path="/integrations/reference/api/identity")) == 404
        finally:
            stop(process)
            listener.close()
            try:
                UPSTREAM_SOCKET.unlink()
            except FileNotFoundError:
                pass
    print("gateway_lab_tests ok")


if __name__ == "__main__":
    skip_or_fail(main)
