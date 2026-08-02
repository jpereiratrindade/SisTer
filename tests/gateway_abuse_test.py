#!/usr/bin/env python3
import json
import re
import ssl

from gateway_lab_support import (
    capture_upstream,
    clear_stick_tables,
    connect_tls,
    read_gateway_log,
    request,
    response_header,
    running_haproxy,
    skip_or_fail,
    stats_command,
    status,
)


def assert_rate_limit(response, retry_after):
    assert status(response) == 429, response[:200]
    assert response_header(response, "Retry-After") == str(retry_after)


def table_usage(name, expected_size):
    output = stats_command(f"show table {name}")
    match = re.search(rf"# table: {name}, type: \w+, size:(\d+), used:(\d+)", output)
    assert match, output
    size, used = (int(value) for value in match.groups())
    assert size == expected_size, output
    assert used <= size, output
    return used


def test_independent_limiters():
    with capture_upstream() as records, running_haproxy(expect_backend=True):
        clear_stick_tables()

        source = "127.10.0.1"
        before = len(records)
        for _ in range(10):
            assert status(request("POST", "/api/auth/login", body=b"{}", source_address=source)) == 200
        assert len(records) == before + 10
        assert_rate_limit(request("POST", "/api/auth/login", body=b"{}", source_address=source), 60)
        assert len(records) == before + 10

        common_source = "127.10.0.2"
        for _ in range(11):
            assert status(request(path="/api/common", source_address=common_source)) == 200

        route_source = "127.10.0.3"
        before = len(records)
        for _ in range(60):
            assert status(request(path="/api/one-route", source_address=route_source)) == 200
        assert_rate_limit(request(path="/api/one-route", source_address=route_source), 60)
        assert len(records) == before + 60
        assert status(request(path="/api/another-route", source_address=route_source)) == 200

        origin_source = "127.10.0.4"
        before = len(records)
        for index in range(120):
            assert status(request(path=f"/api/origin/{index}", source_address=origin_source)) == 200
        assert_rate_limit(request(path="/api/origin/overflow", source_address=origin_source), 60)
        assert len(records) == before + 120

        assert table_usage("sister_rate_global", 1) == 1
        assert table_usage("sister_rate_origin", 128) >= 4
        assert table_usage("sister_rate_origin_route", 512) >= 120
        assert table_usage("sister_rate_login", 128) == 1


def test_global_and_bounded_origin_table():
    with capture_upstream() as records, running_haproxy(expect_backend=True):
        clear_stick_tables()
        before = len(records)
        for index in range(1000):
            source = f"127.20.{index // 100}.{index % 100 + 1}"
            assert status(request(path=f"/api/global/{index}", source_address=source)) == 200
        assert_rate_limit(request(path="/api/global/overflow", source_address="127.20.11.1"), 10)
        assert len(records) == before + 1000
        retained = table_usage("sister_rate_origin", 128)
        assert 0 < retained < 1000


def test_sanitized_structured_logs():
    secret_values = ("bearer-super-secret", "cookie-super-secret", "password-super-secret", "query-super-secret")
    with capture_upstream(), running_haproxy(expect_backend=True):
        clear_stick_tables()
        source = "127.30.0.1"
        headers = [
            ("Authorization", secret_values[0]),
            ("Cookie", f"session={secret_values[1]}"),
            ("X-Sister-Assertion", "signed-secret-material"),
            ("Content-Type", "application/json"),
        ]
        body = json.dumps({"password": secret_values[2]}).encode()
        for _ in range(11):
            response = request(
                "POST",
                f"/api/auth/login?token={secret_values[3]}",
                headers=headers,
                body=body,
                source_address=source,
            )
        assert_rate_limit(response, 60)

    log = read_gateway_log()
    for secret in (*secret_values, "signed-secret-material"):
        assert secret not in log
    records = [json.loads(line) for line in log.splitlines() if line.startswith("{")]
    blocked = [entry for entry in records if entry.get("blocking_rule") == "login_rate"]
    assert blocked, log
    entry = blocked[-1]
    assert entry["result"] == "blocked"
    assert entry["status"] == 429
    assert entry["observed_source"] == source
    assert entry["path"] == "/api/auth/login"
    assert re.fullmatch(r"[0-9a-f]{32}", entry["request_id"])
    for field in ("duration_ms", "queue_ms", "upstream_ms"):
        assert field in entry


def test_connection_isolation():
    connections = []
    with capture_upstream(), running_haproxy(expect_backend=True):
        clear_stick_tables()
        try:
            for _ in range(32):
                connections.append(connect_tls(source_address="127.40.0.1"))
            try:
                extra = connect_tls(source_address="127.40.0.1", timeout=2)
            except (OSError, ssl.SSLError):
                extra = None
            if extra is not None:
                extra.close()
                raise AssertionError("33rd simultaneous connection from one origin was accepted")
            assert status(request(source_address="127.40.0.2")) == 200
            output = stats_command("show table sister_connection_by_origin")
            assert "conn_cur=32" in output, output
        finally:
            for connection in connections:
                connection.close()


def main():
    test_independent_limiters()
    test_global_and_bounded_origin_table()
    test_sanitized_structured_logs()
    test_connection_isolation()
    print("gateway_abuse_tests ok")


if __name__ == "__main__":
    skip_or_fail(main)
