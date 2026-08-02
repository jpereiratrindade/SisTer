#!/usr/bin/env python3
import contextlib
import http.server
import threading
import time

from gateway_lab_support import request, running_haproxy, skip_or_fail, status


class ControlledHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    hold = threading.Event()

    def do_GET(self):
        if self.path == "/slow":
            time.sleep(16)
        elif self.path == "/hold":
            self.hold.wait(timeout=10)
        payload = b'{"ok":true}'
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, _format, *_args):
        pass


@contextlib.contextmanager
def controlled_upstream():
    ControlledHandler.hold.clear()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 8000), ControlledHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield
    finally:
        ControlledHandler.hold.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def wait_for_recovery():
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        response = request(source_address="127.60.0.1")
        if status(response) == 200:
            return
        time.sleep(0.2)
    raise AssertionError("gateway did not recover after upstream returned")


def test_unavailable_and_recovery():
    with running_haproxy():
        response = request(source_address="127.60.0.1")
        assert status(response) == 503
        assert b'{"error":"service_unavailable"}' in response
        with controlled_upstream():
            wait_for_recovery()


def test_slow_upstream():
    with controlled_upstream(), running_haproxy(expect_backend=True):
        response = request(path="/slow", source_address="127.60.0.2", timeout=18)
        assert status(response) == 504, response[:200]
        assert b'{"error":"upstream_timeout"}' in response
        assert status(request(source_address="127.60.0.3")) == 200


def test_bounded_backend_queue():
    results = []

    def send(index):
        try:
            results.append(status(request(path="/hold", source_address=f"127.61.{index // 100}.{index % 100 + 1}")))
        except OSError:
            results.append(0)

    with controlled_upstream(), running_haproxy(expect_backend=True):
        threads = [threading.Thread(target=send, args=(index,)) for index in range(100)]
        for thread in threads:
            thread.start()
        time.sleep(3)
        ControlledHandler.hold.set()
        for thread in threads:
            thread.join(timeout=8)
        assert all(not thread.is_alive() for thread in threads)
        assert 503 in results, results
        assert 200 in results, results
        assert status(request(source_address="127.60.0.4")) == 200


def main():
    test_unavailable_and_recovery()
    test_slow_upstream()
    test_bounded_backend_queue()
    print("gateway_upstream_resilience_tests ok")


if __name__ == "__main__":
    skip_or_fail(main)
