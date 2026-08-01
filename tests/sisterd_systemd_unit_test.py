#!/usr/bin/env python3
import re
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    unit = Path(sys.argv[1])
    document = unit.read_text(encoding="utf-8")

    required_lines = {
        "Environment=SISTER_ENV=production",
        "Environment=SISTER_BIND_HOST=127.0.0.1",
        "Environment=SISTER_ENABLE_LEGACY_PROXY=false",
        "Environment=SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY=false",
        "NoNewPrivileges=yes",
        "PrivateTmp=yes",
        "ProtectSystem=strict",
        "ProtectHome=yes",
        "CapabilityBoundingSet=",
        "AmbientCapabilities=",
        "RestrictAddressFamilies=AF_INET AF_UNIX",
    }
    configured = {line.strip() for line in document.splitlines()}
    missing = sorted(required_lines - configured)
    assert not missing, f"missing hardened systemd settings: {missing}"

    analyzer = shutil.which("systemd-analyze")
    if analyzer:
        result = subprocess.run(
            [analyzer, "security", "--offline=yes", str(unit)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
        )
        assert result.returncode == 0, result.stdout
        match = re.search(r"Overall exposure level[^:]*:\s*([0-9.]+)", result.stdout)
        assert match, result.stdout
        assert float(match.group(1)) <= 4.0, result.stdout

    print("sisterd_systemd_unit_tests ok")


if __name__ == "__main__":
    main()
