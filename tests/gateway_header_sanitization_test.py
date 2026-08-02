#!/usr/bin/env python3
import re
import time

from gateway_lab_support import (
    capture_upstream,
    haproxy_binary,
    request,
    running_haproxy,
    skip_or_fail,
    status,
)


def main():
    haproxy_binary()
    hostile = [
        ("X-Sister-Subject", "admin"),
        ("X-Sister-Capabilities", "*"),
        ("X-Sister-Assertion", "false"),
        ("X-Forwarded-For", "198.51.100.10"),
        ("X-Forwarded-Host", "attacker.test"),
        ("X-Forwarded-Proto", "http"),
        ("Forwarded", "for=198.51.100.10"),
        ("X-Request-ID", "client-chosen"),
        ("Cookie", "session=opaque-test-value"),
    ]
    with capture_upstream() as records, running_haproxy(expect_backend=True):
        assert status(request(path="/capture", headers=hostile)) == 200
        deadline = time.monotonic() + 2
        while not any(record[1] == "/capture" for record in records) and time.monotonic() < deadline:
            time.sleep(0.01)
        captures = [record for record in records if record[1] == "/capture"]
        assert len(captures) == 1, len(captures)
        _, _, raw_headers, _ = captures[0]
        headers = {name.lower(): value for name, value in raw_headers}
        assert not any(name.startswith("x-sister-") for name in headers), headers
        assert "forwarded" not in headers
        assert headers["x-forwarded-for"] == "127.0.0.1"
        assert headers["x-forwarded-host"] == "sister-gateway.test"
        assert headers["x-forwarded-proto"] == "https"
        assert re.fullmatch(r"[0-9a-f]{32}", headers["x-request-id"]), headers["x-request-id"]
        assert headers["x-request-id"] != "client-chosen"
        assert headers.get("cookie") == "session=opaque-test-value"
    print("gateway_header_sanitization_tests ok")


if __name__ == "__main__":
    skip_or_fail(main)
