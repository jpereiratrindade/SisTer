#!/usr/bin/env python3
import re
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    unit = Path(sys.argv[1])
    document = unit.read_text(encoding="utf-8")
    configured = {line.strip() for line in document.splitlines()}
    required = {
        "Requires=sisterd.socket",
        "After=sisterd.socket network.target",
        "Type=notify",
        "User=sister-gateway",
        "Group=sister-gateway",
        "SupplementaryGroups=haproxy",
        "RuntimeDirectory=sister-gateway",
        "RuntimeDirectoryMode=0750",
        "NoNewPrivileges=yes",
        "PrivateTmp=yes",
        "ProtectSystem=strict",
        "ProtectHome=yes",
        "CapabilityBoundingSet=",
        "AmbientCapabilities=",
        "RestrictAddressFamilies=AF_INET AF_UNIX",
    }
    missing = sorted(required - configured)
    assert not missing, f"missing governed gateway settings: {missing}"
    binary = "/usr/local/sbin/haproxy-3.2.22"
    config = "/etc/sister/gateway/haproxy.cfg"
    assert f"ConditionFileIsExecutable={binary}" in configured
    assert f"ExecStartPre={binary} -c -q -f {config}" in configured
    assert (
        f"ExecStart={binary} -Ws -f {config} "
        "-p /run/sister-gateway/haproxy.pid"
    ) in configured
    assert "0.0.0.0" not in document
    assert "127.0.0.1:8000" not in document

    analyzer = shutil.which("systemd-analyze")
    if analyzer:
        security = subprocess.run(
            [analyzer, "security", "--offline=yes", str(unit)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
        )
        assert security.returncode == 0, security.stdout
        match = re.search(r"Overall exposure level[^:]*:\s*([0-9.]+)", security.stdout)
        assert match and float(match.group(1)) <= 4.0, security.stdout

    print("sister_gateway_systemd_unit_tests ok")


if __name__ == "__main__":
    main()
