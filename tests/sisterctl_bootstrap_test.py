#!/usr/bin/env python3
import os
import pty
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run_bootstrap(executable, auth_file, password):
    master, slave = pty.openpty()
    environment = os.environ.copy()
    environment["SISTER_AUTH_FILE"] = str(auth_file)
    process = subprocess.Popen(
        [executable, "auth", "bootstrap-admin", "Bootstrap Admin", "bootstrap@test.invalid"],
        env=environment,
        stdin=slave,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        close_fds=True,
    )
    os.close(slave)
    try:
        captured = bytearray()

        def wait_for_prompt(prompt):
            deadline = time.monotonic() + 5
            while prompt not in captured:
                remaining = deadline - time.monotonic()
                assert remaining > 0, captured.decode(errors="replace")
                ready, _, _ = select.select([process.stdout], [], [], remaining)
                assert ready, captured.decode(errors="replace")
                chunk = os.read(process.stdout.fileno(), 1024)
                assert chunk, captured.decode(errors="replace")
                captured.extend(chunk)

        wait_for_prompt(b"Nova senha administrativa: ")
        os.write(master, f"{password}\n".encode())
        wait_for_prompt(b"Confirme a senha: ")
        os.write(master, f"{password}\n".encode())
        remainder, _ = process.communicate(timeout=10)
        captured.extend(remainder)
        return process.returncode, captured.decode(errors="replace")
    finally:
        os.close(master)


def main():
    executable = sys.argv[1]
    with tempfile.TemporaryDirectory(prefix="sisterctl-bootstrap-") as temporary:
        auth_file = Path(temporary) / "auth.tsv"
        status, output = run_bootstrap(executable, auth_file, "bootstrap-password-123")
        assert status == 0, output
        assert "administrator created: bootstrap@test.invalid" in output, output
        persisted = auth_file.read_text(encoding="utf-8")
        assert "bootstrap@test.invalid" in persisted
        assert "\tadmin\t" in persisted
        assert auth_file.stat().st_mode & 0o077 == 0

        status, output = run_bootstrap(executable, auth_file, "another-password-123")
        assert status == 1, output
        assert "administrator bootstrap is closed" in output, output

    print("sisterctl_bootstrap_tests ok")


if __name__ == "__main__":
    main()
