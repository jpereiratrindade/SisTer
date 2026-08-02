#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess

from gateway_lab_support import ROOT, RUN_DIR, lab_environment, request, running_haproxy, skip_or_fail, status


def main():
    with running_haproxy():
        assert status(request()) == 503

    environment = lab_environment()
    environment["GATEWAY_TLS_PEM"] = str(RUN_DIR / "missing.pem")
    missing = subprocess.run(
        [str(ROOT / "scripts/render_gateway_config.py")],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert missing.returncode != 0
    assert "regular file" in missing.stderr

    pem = RUN_DIR / "gateway-lab.pem"
    old_mode = pem.stat().st_mode & 0o777
    try:
        os.chmod(pem, 0o644)
        environment["GATEWAY_TLS_PEM"] = str(pem)
        permissive = subprocess.run(
            [str(ROOT / "scripts/render_gateway_config.py")],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert permissive.returncode != 0
        assert "permissions" in permissive.stderr
    finally:
        os.chmod(pem, old_mode)

    invalid = RUN_DIR / "invalid.cfg"
    invalid.write_text("this is not HAProxy configuration\n", encoding="utf-8")
    os.chmod(invalid, 0o640)
    checked = subprocess.run(
        [environment["GATEWAY_HAPROXY_BIN"], "-c", "-V", "-f", str(invalid)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert checked.returncode != 0
    print("gateway_failure_tests ok")


if __name__ == "__main__":
    skip_or_fail(main)
