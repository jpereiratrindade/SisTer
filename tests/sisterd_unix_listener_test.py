#!/usr/bin/env python3
import errno
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = Path(__file__).with_name("socket_activation_launcher.py")


def environment(web_root, auth_file, socket_path):
    result = os.environ.copy()
    result.update(
        {
            "SISTER_ENV": "test",
            "SISTER_LISTENER_MODE": "systemd-unix",
            "SISTER_ACTIVATED_SOCKET_PATH": str(socket_path),
            "SISTER_WEB_ROOT": str(web_root),
            "SISTER_AUTH_FILE": str(auth_file),
            "SISTER_ENABLE_HTTP_BOOTSTRAP": "false",
            "SISTER_ENABLE_LEGACY_PROXY": "false",
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY": "false",
            "SISTER_ENABLE_NEXO_SIGNED_INTEGRATION": "false",
        }
    )
    for name in ("SISTER_BIND_HOST", "SISTER_PORT", "LISTEN_PID", "LISTEN_FDS", "LISTEN_FDNAMES"):
        result.pop(name, None)
    return result


def create_listener(path, *, listening=True, socket_type=socket.SOCK_STREAM):
    listener = socket.socket(socket.AF_UNIX, socket_type)
    listener.bind(str(path))
    os.chmod(path, 0o600)
    if listening:
        listener.listen(256)
    return listener


def start(executable, listener_fds, env):
    descriptors = ",".join(str(fd) for fd in listener_fds)
    return subprocess.Popen(
        [sys.executable, str(LAUNCHER), descriptors, executable],
        cwd=ROOT,
        env=env,
        pass_fds=tuple(listener_fds),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def exchange(path, request=b"GET /api/health HTTP/1.1\r\nHost: sister-gateway.test\r\nConnection: close\r\n\r\n"):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(2)
        connection.connect(str(path))
        connection.sendall(request)
        response = bytearray()
        while True:
            chunk = connection.recv(65536)
            if not chunk:
                break
            response.extend(chunk)
    return bytes(response)


def wait_for_health(process, path):
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(process.stdout.read() if process.stdout else "sisterd exited")
        try:
            if exchange(path).startswith(b"HTTP/1.1 200"):
                return
        except OSError:
            pass
        time.sleep(0.05)
    raise AssertionError("activated sisterd did not become ready")


def stop(process):
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def assert_fails(executable, env, fragment, listener_fds=()):
    process = start(executable, listener_fds, env)
    output, _ = process.communicate(timeout=5)
    assert process.returncode != 0, output
    assert fragment in output, (fragment, output)


def assert_direct_fails(executable, env, fragment):
    completed = subprocess.run(
        [executable],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=5,
        check=False,
    )
    assert completed.returncode != 0, completed.stdout
    assert fragment in completed.stdout, (fragment, completed.stdout)


def main():
    executable, web_root = sys.argv[1:3]
    run_root = ROOT / ".run"
    run_root.mkdir(mode=0o700, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="iso-01-", dir=run_root) as temporary:
        directory = Path(temporary)
        socket_path = directory / "sisterd.sock"
        auth_file = directory / "auth.tsv"
        listener = create_listener(socket_path)
        env = environment(web_root, auth_file, socket_path)
        process = start(executable, [listener.fileno()], env)
        try:
            wait_for_health(process, socket_path)
            assert exchange(socket_path).startswith(b"HTTP/1.1 200")
            try:
                socket.create_connection(("127.0.0.1", 8000), timeout=0.2)
            except OSError:
                pass
            else:
                raise AssertionError("sisterd exposed a TCP listener on port 8000")

            inode = socket_path.stat().st_ino
            mode = socket_path.stat().st_mode & 0o777
            os.chmod(socket_path, 0)
            try:
                exchange(socket_path)
            except PermissionError as exc:
                assert exc.errno == errno.EACCES
            else:
                raise AssertionError("mode 000 Unix socket remained connectable")
            os.chmod(socket_path, mode)
        finally:
            stop(process)

        replacement = start(executable, [listener.fileno()], env)
        try:
            wait_for_health(replacement, socket_path)
            assert socket_path.stat().st_ino == inode
            assert socket_path.stat().st_mode & 0o777 == mode
        finally:
            stop(replacement)

        wrong_path = directory / "wrong.sock"
        wrong_listener = create_listener(wrong_path)
        try:
            assert_fails(executable, environment(web_root, auth_file, socket_path), "path does not match", [wrong_listener.fileno()])
        finally:
            wrong_listener.close()
            wrong_path.unlink()

        second_path = directory / "second.sock"
        second = create_listener(second_path)
        try:
            assert_fails(executable, env, "exactly one descriptor", [listener.fileno(), second.fileno()])
        finally:
            second.close()
            second_path.unlink()

        not_listening_path = directory / "not-listening.sock"
        not_listening = create_listener(not_listening_path, listening=False)
        try:
            assert_fails(executable, environment(web_root, auth_file, not_listening_path), "not listening", [not_listening.fileno()])
        finally:
            not_listening.close()
            not_listening_path.unlink()

        bad_name = env.copy()
        bad_name["TEST_LISTEN_FDNAMES"] = "unexpected"
        assert_fails(executable, bad_name, "missing or unexpected descriptor name", [listener.fileno()])

        missing_name = env.copy()
        missing_name["TEST_OMIT_LISTEN_FDNAMES"] = "1"
        assert_fails(executable, missing_name, "missing or unexpected descriptor name", [listener.fileno()])

        zero = env.copy()
        zero["TEST_LISTEN_FDS"] = "0"
        assert_fails(executable, zero, "exactly one descriptor", [listener.fileno()])

        closed = env.copy()
        closed["TEST_LISTEN_FDS"] = "1"
        closed["TEST_LISTEN_FDNAMES"] = "sisterd-http"
        assert_fails(executable, closed, "descriptor 3 is not open")

        wrong_pid = env.copy()
        wrong_pid["TEST_LISTEN_PID"] = "1"
        assert_fails(executable, wrong_pid, "LISTEN_PID does not match", [listener.fileno()])

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_listener:
            tcp_listener.bind(("127.0.0.1", 0))
            tcp_listener.listen(1)
            assert_fails(executable, env, "descriptor is not AF_UNIX", [tcp_listener.fileno()])

        datagram_path = directory / "datagram.sock"
        datagram = create_listener(datagram_path, listening=False, socket_type=socket.SOCK_DGRAM)
        try:
            assert_fails(executable, environment(web_root, auth_file, datagram_path), "not SOCK_STREAM", [datagram.fileno()])
        finally:
            datagram.close()
            datagram_path.unlink()

        fallback = environment(web_root, auth_file, socket_path)
        fallback["SISTER_ALLOW_TCP_FALLBACK"] = "true"
        assert_fails(executable, fallback, "fallback is forbidden", [listener.fileno()])

        occupied = directory / "occupied.sock"
        occupied.write_text("not a socket", encoding="utf-8")
        try:
            create_listener(occupied)
        except OSError as exc:
            assert exc.errno == errno.EADDRINUSE
        else:
            raise AssertionError("regular file was replaced by a Unix listener")
        occupied.unlink()

        target = directory / "symlink-target"
        target.write_text("target", encoding="utf-8")
        occupied.symlink_to(target)
        try:
            create_listener(occupied)
        except OSError as exc:
            assert exc.errno == errno.EADDRINUSE
        else:
            raise AssertionError("symlink was replaced by a Unix listener")
        occupied.unlink()
        target.unlink()

        production = environment(web_root, auth_file, Path("/run/sister/sisterd.sock"))
        production["SISTER_ENV"] = "production"
        assert_direct_fails(executable, production, "missing socket activation variable")
        production["SISTER_LISTENER_MODE"] = "tcp-loopback"
        assert_direct_fails(executable, production, "requires the systemd-activated Unix listener")

        listener.close()
        socket_path.unlink()

    print("sisterd_unix_listener_tests ok")


if __name__ == "__main__":
    main()
