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

        wrong_sni = tls_context()
        wrong_sni.check_hostname = False
        try:
            tls_exchange(b"", context=wrong_sni, server_hostname="unknown.test")
        except (ssl.SSLError, ConnectionResetError, OSError):
            pass
        else:
            raise AssertionError("an unknown SNI was accepted")

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
            b"GET /authority-host-identical HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Host: sister-gateway.test\r\nConnection: close\r\n\r\n"
        )[0]
        # HAProxy 3.2.22 normalizes two identical Host lines into one HTX field
        # before the ACL. SEC-03B-R accepts this restricted divergence only when
        # the upstream authority is rebuilt to the single canonical Host.
        assert status(duplicate_host) == 200
        duplicate_host_records = [record for record in records if record[1] == "/authority-host-identical"]
        assert len(duplicate_host_records) == 1
        effective_hosts = [
            value for name, value in duplicate_host_records[0][2] if name.lower() == "host"
        ]
        assert effective_hosts == ["sister-gateway.test"], effective_hosts

        for first_host, second_host in (
            ("sister-gateway.test", "unknown.test"),
            ("unknown.test", "sister-gateway.test"),
        ):
            divergent_host = tls_exchange(
                b"GET /authority-host-divergent HTTP/1.1\r\n"
                + f"Host: {first_host}\r\nHost: {second_host}\r\n".encode("ascii")
                + b"Connection: close\r\n\r\n"
            )[0]
            assert status(divergent_host) == 400
        assert not any(record[1] == "/authority-host-divergent" for record in records)

        assert status(request(headers=[("Host", "sister-gateway.test:9443")])) == 403
        assert status(request(headers=[("Host", "sister-gateway.test:8443")])) == 200

        absolute_unknown = tls_exchange(
            b"GET https://unknown.test/authority-absolute HTTP/1.1\r\n"
            b"Host: sister-gateway.test\r\nConnection: close\r\n\r\n"
        )[0]
        assert status(absolute_unknown) == 400
        absolute_canonical = tls_exchange(
            b"GET https://sister-gateway.test/authority-absolute HTTP/1.1\r\n"
            b"Host: unknown.test\r\nConnection: close\r\n\r\n"
        )[0]
        assert status(absolute_canonical) == 400
        absolute_records = [record for record in records if record[1] == "/authority-absolute"]
        assert not absolute_records
        assert status(request(headers=[("Host", "*.sister-gateway.test")])) == 403
        assert status(request(method="OPTIONS")) == 405

        assert status(request(method="POST", path="/upload", body=b"a" * 1048576)) == 200
        oversized_upload = tls_exchange(
            b"POST /upload HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Content-Length: 1048577\r\nConnection: close\r\n\r\n",
            stop_at_http_message=True,
        )[0]
        assert status(oversized_upload) == 413
        assert status(request(method="POST", path="/api/auth/login", body=b"a" * 65536)) == 200
        oversized_auth = tls_exchange(
            b"POST /api/auth/login HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Content-Length: 65537\r\nConnection: close\r\n\r\n",
            stop_at_http_message=True,
        )[0]
        assert status(oversized_auth) == 413
        duplicate_length = tls_exchange(
            b"POST /framing-identical HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Content-Length: 5\r\nContent-Length: 5\r\nConnection: close\r\n\r\nhello"
        )[0]
        # RFC 9112 permits equal valid values to become one effective length.
        assert status(duplicate_length) == 200
        identical_length_records = [record for record in records if record[1] == "/framing-identical"]
        assert len(identical_length_records) == 1
        effective_lengths = [
            value
            for name, value in identical_length_records[0][2]
            if name.lower() == "content-length"
        ]
        assert effective_lengths == ["5"], effective_lengths
        assert identical_length_records[0][3] == b"hello"
        conflicting_length = tls_exchange(
            b"POST /framing-conflicting HTTP/1.1\r\nHost: sister-gateway.test\r\n"
            b"Content-Length: 0\r\nContent-Length: 1\r\nConnection: close\r\n\r\n"
        )[0]
        assert status(conflicting_length) == 400
        assert not any(record[1] == "/framing-conflicting" for record in records)
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
        for stripped_path in ("/ws-upgrade", "/ws-connection"):
            stripped_records = [record for record in records if record[1] == stripped_path]
            assert len(stripped_records) == 1
            effective_names = {name.lower() for name, _ in stripped_records[0][2]}
            assert "upgrade" not in effective_names
            assert "connection" not in effective_names
    print("gateway_protocol_tests ok")


if __name__ == "__main__":
    skip_or_fail(main)
