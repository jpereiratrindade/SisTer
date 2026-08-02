#!/usr/bin/env python3
import socket
import time

from gateway_lab_support import (
    HOST,
    capture_upstream,
    connect_tls,
    request,
    running_haproxy,
    skip_or_fail,
    status,
)


def assert_closed(connection):
    connection.settimeout(2)
    try:
        data = connection.recv(65536)
    except (ConnectionResetError, OSError):
        return
    assert not data or data.startswith((b"HTTP/1.1 400", b"HTTP/1.1 408")), data[:200]


def read_response(connection):
    response = bytearray()
    while b"\r\n\r\n" not in response:
        response.extend(connection.recv(65536))
    head, body = bytes(response).split(b"\r\n\r\n", 1)
    length = 0
    for line in head.split(b"\r\n")[1:]:
        if line.lower().startswith(b"content-length:"):
            length = int(line.split(b":", 1)[1])
    while len(body) < length:
        body += connection.recv(65536)
    return head + b"\r\n\r\n" + body[:length]


def main():
    with capture_upstream(), running_haproxy(expect_backend=True):
        with socket.create_connection(("127.0.0.1", 8443), timeout=2) as no_handshake:
            time.sleep(5.5)
            assert_closed(no_handshake)

        with connect_tls(source_address="127.50.0.1") as slow_headers:
            slow_headers.sendall(f"GET /api/health HTTP/1.1\r\nHost: {HOST}".encode())
            time.sleep(5.5)
            assert_closed(slow_headers)

        with connect_tls(source_address="127.50.0.2", timeout=18) as partial_body:
            partial_body.sendall(
                f"POST /api/partial HTTP/1.1\r\nHost: {HOST}\r\nContent-Length: 10\r\n\r\nx".encode()
            )
            time.sleep(15.5)
            assert_closed(partial_body)

        with connect_tls(source_address="127.50.0.3") as keep_alive:
            keep_alive.sendall(
                f"GET /api/health HTTP/1.1\r\nHost: {HOST}\r\nConnection: keep-alive\r\n\r\n".encode()
            )
            assert status(read_response(keep_alive)) == 200
            time.sleep(2.5)
            assert_closed(keep_alive)

        assert status(request(source_address="127.50.0.4")) == 200

    print("gateway_slow_client_tests ok")


if __name__ == "__main__":
    skip_or_fail(main)
