#!/usr/bin/env python3
import contextlib
import http.server
import os
from pathlib import Path
import signal
import socket
import socketserver
import ssl
import subprocess
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / ".run/gateway-tests" / str(os.getpid())
HOST = "sister-gateway.test"
UPSTREAM_SOCKET = RUN_DIR / "sisterd.sock"
RUN_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)


class LabUnavailable(RuntimeError):
    pass


def haproxy_binary():
    raw = os.environ.get("GATEWAY_HAPROXY_BIN", "")
    path = Path(raw)
    if not raw or not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        raise LabUnavailable("set GATEWAY_HAPROXY_BIN to an absolute executable HAProxy 3.2.22+ path")
    return path


def lab_environment():
    binary = haproxy_binary()
    environment = os.environ.copy()
    environment.update(
        {
            "GATEWAY_HAPROXY_BIN": str(binary),
            "GATEWAY_TLS_PEM": str(RUN_DIR / "gateway-lab.pem"),
            "GATEWAY_ALLOWED_HOST": HOST,
            "GATEWAY_CANONICAL_HOST": HOST,
            "GATEWAY_RUN_ROOT": str(RUN_DIR),
            "GATEWAY_UPSTREAM_SOCKET": str(UPSTREAM_SOCKET),
        }
    )
    return environment


def prepare_runtime():
    environment = lab_environment()
    try:
        (RUN_DIR / "haproxy.sock").unlink()
    except FileNotFoundError:
        pass
    subprocess.run(
        [str(ROOT / "scripts/create_gateway_lab_certificate.sh"), HOST],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        check=True,
    )
    subprocess.run(
        [str(ROOT / "scripts/render_gateway_config.py"), "--output", str(RUN_DIR / "haproxy.cfg")],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        check=True,
    )
    subprocess.run(
        [str(ROOT / "scripts/validate_gateway_config.sh"), str(RUN_DIR / "haproxy.cfg")],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        check=True,
    )
    return environment


def tls_context(*, maximum=None, alpn=("http/1.1",)):
    context = ssl.create_default_context(cafile=str(RUN_DIR / "ca-lab.crt"))
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    if maximum is not None:
        context.maximum_version = maximum
    if alpn:
        context.set_alpn_protocols(list(alpn))
    return context


def connect_tls(*, context=None, server_hostname=HOST, source_address=None, timeout=4):
    context = context or tls_context()
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw.settimeout(timeout)
    try:
        if source_address:
            raw.bind((source_address, 0))
        raw.connect(("127.0.0.1", 8443))
        connection = context.wrap_socket(raw, server_hostname=server_hostname)
        connection.settimeout(timeout)
        return connection
    except BaseException:
        raw.close()
        raise


def tls_exchange(request, *, context=None, server_hostname=HOST, source_address=None, timeout=4):
    with connect_tls(
        context=context,
        server_hostname=server_hostname,
        source_address=source_address,
        timeout=timeout,
    ) as connection:
        connection.sendall(request)
        response = bytearray()
        while True:
            try:
                chunk = connection.recv(65536)
            except (ConnectionResetError, ssl.SSLError):
                break
            if not chunk:
                break
            response.extend(chunk)
        return bytes(response), connection.version(), connection.selected_alpn_protocol()


def request(method="GET", path="/api/health", headers=None, body=b"", *, source_address=None, timeout=4):
    supplied = list(headers or [])
    names = {name.lower() for name, _ in supplied}
    if "host" not in names:
        supplied.insert(0, ("Host", HOST))
    if body and "content-length" not in names:
        supplied.append(("Content-Length", str(len(body))))
    supplied.append(("Connection", "close"))
    head = f"{method} {path} HTTP/1.1\r\n".encode("ascii")
    head += b"".join(f"{name}: {value}\r\n".encode("iso-8859-1") for name, value in supplied)
    return tls_exchange(head + b"\r\n" + body, source_address=source_address, timeout=timeout)[0]


def status(response):
    if not response.startswith(b"HTTP/1.1 "):
        raise AssertionError(response[:200])
    return int(response.split(b" ", 2)[1])


def response_header(response, name):
    expected = name.lower().encode("ascii") + b":"
    for line in response.split(b"\r\n")[1:]:
        if line.lower().startswith(expected):
            return line.split(b":", 1)[1].strip().decode("ascii")
    return None


def stats_command(command):
    path = RUN_DIR / "haproxy.sock"
    deadline = time.monotonic() + 4
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(4)
        client.connect(str(path))
        client.sendall(command.rstrip().encode("ascii") + b"\n")
        client.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            chunk = client.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
    return b"".join(chunks).decode("utf-8", errors="replace")


def clear_stick_tables():
    for table in (
        "sister_connection_by_origin",
        "sister_rate_global",
        "sister_rate_origin",
        "sister_rate_origin_route",
        "sister_rate_login",
    ):
        stats_command(f"clear table {table}")


def read_gateway_log():
    path = RUN_DIR / "haproxy-test.log"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def wait_for_tls(process, expected_status=None):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError(f"HAProxy exited before becoming ready: {output}")
        try:
            response = request()
            if response and (expected_status is None or status(response) == expected_status):
                return
        except OSError:
            pass
        time.sleep(0.1)
    raise AssertionError("HAProxy did not become ready")


@contextlib.contextmanager
def running_haproxy(*, expect_backend=False):
    environment = prepare_runtime()
    log_path = RUN_DIR / "haproxy-test.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [environment["GATEWAY_HAPROXY_BIN"], "-Ws", "-f", str(RUN_DIR / "haproxy.cfg")],
            cwd=ROOT,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_for_tls(process, 200 if expect_backend else None)
            yield process
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            try:
                (RUN_DIR / "haproxy.sock").unlink()
            except FileNotFoundError:
                pass


class CaptureHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    records = []

    def handle_request(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        if self.path != "/api/health":
            self.records.append((self.command, self.path, list(self.headers.items()), body))
        payload = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError):
                pass

    do_GET = handle_request
    do_HEAD = handle_request
    do_POST = handle_request
    do_PUT = handle_request
    do_PATCH = handle_request
    do_DELETE = handle_request

    def log_message(self, _format, *_args):
        pass


class ThreadingUnixHTTPServer(http.server.ThreadingHTTPServer):
    address_family = socket.AF_UNIX

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name = "localhost"
        self.server_port = 0


@contextlib.contextmanager
def capture_upstream():
    CaptureHandler.records = []
    try:
        UPSTREAM_SOCKET.unlink()
    except FileNotFoundError:
        pass
    server = ThreadingUnixHTTPServer(str(UPSTREAM_SOCKET), CaptureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield CaptureHandler.records
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        try:
            UPSTREAM_SOCKET.unlink()
        except FileNotFoundError:
            pass


def skip_or_fail(main):
    try:
        main()
    except LabUnavailable as exc:
        print(f"SKIP: {exc}")
        raise SystemExit(77)
