#!/usr/bin/env python3
import http.client
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time


def reserve_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for_server(port, process):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("sisterd exited before accepting requests")
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=0.2)
            connection.request("GET", "/api/health")
            response = connection.getresponse()
            response.read()
            connection.close()
            if response.status == 200:
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("sisterd did not become ready")


def start_sisterd(executable, web_root, port, clima_port, auth_file):
    environment = os.environ.copy()
    environment.update(
        {
            "SISTER_ENV": "development",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_AUTH_FILE": auth_file,
            "SISTER_CLIMA_PORT": str(clima_port),
            "SISTER_COOKIE_SECURE": "false",
            "SISTER_DATABASE_URL": "",
            "SISTER_WORKERS": "4",
            "SISTER_ENABLE_LEGACY_PROXY": "true",
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "true",
        }
    )
    process = subprocess.Popen(
        [executable, str(port), web_root],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    wait_for_server(port, process)
    return process


def stop_sisterd(process):
    if process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def register(port):
    body = '{"name":"Proxy Test","email":"proxy@test.invalid","password":"proxy-test-password"}'
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    connection.request("POST", "/api/auth/register", body, {"Content-Type": "application/json"})
    response = connection.getresponse()
    response.read()
    assert response.status == 201, response.status
    cookie = response.getheader("Set-Cookie").split(";", 1)[0]
    connection.close()
    return cookie


def assert_session(port, cookie):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    connection.request("GET", "/api/me", headers={"Cookie": cookie})
    response = connection.getresponse()
    body = response.read()
    connection.close()
    assert response.status == 200, (response.status, body)


def run_mock_websocket(port, captured, ready):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
        listener.listen(1)
        ready.set()
        connection, _ = listener.accept()
        with connection:
            request = b""
            while b"\r\n\r\n" not in request:
                chunk = connection.recv(8192)
                if not chunk:
                    break
                request += chunk
            captured.append(request.decode("iso-8859-1"))
            connection.sendall(
                b"HTTP/1.1 101 Switching Protocols\r\n"
                b"Upgrade: websocket\r\n"
                b"Connection: Upgrade\r\n"
                b"Sec-WebSocket-Accept: test\r\n\r\n"
            )


def websocket_request(port, cookie):
    with socket.create_connection(("127.0.0.1", port), timeout=2) as connection:
        request = (
            "GET /integrations/clima/_stcore/stream HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            "Connection: keep-alive, Upgrade\r\n"
            "Upgrade: websocket\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            f"Cookie: unrelated=value; {cookie}\r\n\r\n"
        )
        connection.sendall(request.encode("ascii"))
        response = connection.recv(4096)
    assert response.startswith(b"HTTP/1.1 101 "), response


def main():
    executable, web_root = sys.argv[1:3]
    sister_port = reserve_port()
    clima_port = reserve_port()
    captured = []
    ready = threading.Event()
    mock = threading.Thread(
        target=run_mock_websocket, args=(clima_port, captured, ready), daemon=True
    )
    mock.start()
    assert ready.wait(timeout=2)

    with tempfile.TemporaryDirectory(prefix="sister-clima-proxy-test-") as temporary:
        auth_file = os.path.join(temporary, "auth.tsv")
        process = start_sisterd(executable, web_root, sister_port, clima_port, auth_file)
        try:
            cookie = register(sister_port)
            websocket_request(sister_port, cookie)
            mock.join(timeout=2)
            assert not mock.is_alive(), "mock WebSocket did not finish"
            assert len(captured) == 1
            upstream = captured[0].lower()
            assert upstream.startswith("get /_stcore/stream http/1.1\r\n")
            assert f"cookie: {cookie.lower()}\r\n" in upstream
            assert "cookie: unrelated=value" not in upstream
            assert f"x-forwarded-host: 127.0.0.1:{sister_port}\r\n" in upstream
            assert "x-forwarded-proto: http\r\n" in upstream
            assert "x-sister-subject: " in upstream
        finally:
            stop_sisterd(process)

        process = start_sisterd(executable, web_root, sister_port, clima_port, auth_file)
        try:
            assert_session(sister_port, cookie)
        finally:
            stop_sisterd(process)

    print("sisterd_clima_proxy_tests ok")


if __name__ == "__main__":
    main()
