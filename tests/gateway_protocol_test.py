#!/usr/bin/env python3
import socket
import ssl

from gateway_lab_support import (
    capture_upstream,
    haproxy_binary,
    request,
    running_haproxy,
    skip_or_fail,
    status,
    tls_context,
    tls_exchange,
)


def main():
    haproxy_binary()
    with capture_upstream() as records, running_haproxy(expect_backend=True):
        response, version, alpn = tls_exchange(
            b"GET /api/health HTTP/1.1\r\nHost: sister-gateway.test\r\nConnection: close\r\n\r\n"
        )
        assert status(response) == 200
        assert version == "TLSv1.3", version
        assert alpn == "http/1.1", alpn

        tls12 = tls_context(maximum=ssl.TLSVersion.TLSv1_2)
        try:
            tls_exchange(b"", context=tls12)
        except (ssl.SSLError, ConnectionResetError, OSError):
            pass
        else:
            raise AssertionError("TLS 1.2 was accepted")

        h2_only = tls_context(alpn=("h2",))
        _, negotiated_version, negotiated_alpn = tls_exchange(
            b"GET /api/health HTTP/1.1\r\nHost: sister-gateway.test\r\nConnection: close\r\n\r\n",
            context=h2_only,
        )
        assert negotiated_version == "TLSv1.3"
        assert negotiated_alpn is None, negotiated_alpn

        with socket.create_connection(("127.0.0.1", 8443), timeout=2) as plain:
            plain.sendall(b"GET / HTTP/1.1\r\nHost: sister-gateway.test\r\n\r\n")
            try:
                plaintext_response = plain.recv(256)
            except ConnectionResetError:
                plaintext_response = b""
        assert not plaintext_response.startswith(b"HTTP/"), plaintext_response

        assert status(request(headers=[("Host", "unknown.test")])) == 403
        assert status(request(headers=[])) == 200
        missing_host = tls_exchange(b"GET /api/health HTTP/1.1\r\nConnection: close\r\n\r\n")[0]
        assert status(missing_host) == 400
        duplicate_host = tls_exchange(
            b"GET /api/health HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Host: sister-gateway.test\r\nConnection: close\r\n\r\n"
        )[0]
        # HAProxy 3.2.22 normalizes two identical Host lines into one HTX field
        # before the ACL. Preserve the observed gap as explicit lab evidence.
        assert status(duplicate_host) == 200
        assert status(request(headers=[("Host", "*.sister-gateway.test")])) == 403
        assert status(request(method="OPTIONS")) == 405

        assert status(request(method="POST", path="/upload", body=b"a" * 1048576)) == 200
        assert status(
            request(
                method="POST",
                path="/upload",
                body=b"a" * 1048577,
            )
        ) == 413
        assert status(request(method="POST", path="/api/auth/login", body=b"a" * 65536)) == 200
        assert status(
            request(
                method="POST",
                path="/api/auth/login",
                body=b"a" * 65537,
            )
        ) == 413
        duplicate_length = tls_exchange(
            b"POST /upload HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Content-Length: 0\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
        )[0]
        # Identical Content-Length lines are likewise normalized before ACLs.
        assert status(duplicate_length) == 200
        conflicting_length = tls_exchange(
            b"POST /upload HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Content-Length: 0\r\nContent-Length: 1\r\nConnection: close\r\n\r\n"
        )[0]
        assert status(conflicting_length) == 400
        chunked = tls_exchange(
            b"POST /upload HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Transfer-Encoding: chunked\r\nConnection: close\r\n\r\n0\r\n\r\n"
        )[0]
        assert status(chunked) == 400
        conflicting_framing = tls_exchange(
            b"POST /upload HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Content-Length: 5\r\nTransfer-Encoding: chunked\r\n"
            b"Connection: close\r\n\r\n0\r\n\r\n"
        )[0]
        assert status(conflicting_framing) == 400

        too_many = [(f"X-Lab-{index}", "x") for index in range(70)]
        assert status(request(headers=too_many)) == 400

        websocket_requests = (
            (b"/ws-upgrade", b"Upgrade: websocket\r\nConnection: close", 200),
            (b"/ws-connection", b"Connection: Upgrade", 200),
            (b"/ws-complete", b"Upgrade: websocket\r\nConnection: Upgrade", 400),
        )
        for websocket_path, websocket_headers, observed_status in websocket_requests:
            response = tls_exchange(
                b"GET " + websocket_path + b" HTTP/1.1\r\nHost: sister-gateway.test\r\n"
                + websocket_headers
                + b"\r\n\r\n"
            )[0]
            # Standalone hop-by-hop fields are normalized out before the ACL;
            # the complete handshake is rejected by HAProxy's HTTP parser.
            assert status(response) == observed_status
        assert not any(record[1] == "/ws-complete" for record in records)
    print("gateway_protocol_tests ok")


if __name__ == "__main__":
    skip_or_fail(main)
