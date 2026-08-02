#!/usr/bin/env python3
import re
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    service = Path(sys.argv[1])
    socket_unit = Path(sys.argv[2])
    tmpfiles = Path(sys.argv[3])
    document = service.read_text(encoding="utf-8")

    required_lines = {
        "Environment=SISTER_ENV=production",
        "Environment=SISTER_LISTENER_MODE=systemd-unix",
        "Environment=SISTER_ACTIVATED_SOCKET_PATH=/run/sister/sisterd.sock",
        "Environment=SISTER_ENABLE_HTTP_BOOTSTRAP=false",
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
    assert "SISTER_BIND_HOST" not in document
    assert "SISTER_PORT" not in document
    assert "EnvironmentFile=/etc/sister/sister.env" in document
    assert "Environment=SISTER_ENABLE_NEXO_SIGNED_INTEGRATION" not in document
    assert "ExecStart=/opt/sister/build/apps/sisterd/sisterd\n" in document

    socket_document = socket_unit.read_text(encoding="utf-8")
    socket_required = {
        "ListenStream=/run/sister/sisterd.sock",
        "FileDescriptorName=sisterd-http",
        "Accept=no",
        "SocketUser=sister",
        "SocketGroup=haproxy",
        "SocketMode=0660",
        "RemoveOnStop=yes",
    }
    configured_socket = {line.strip() for line in socket_document.splitlines()}
    missing_socket = sorted(socket_required - configured_socket)
    assert not missing_socket, f"missing socket isolation settings: {missing_socket}"
    assert "ListenStream=127.0.0.1" not in socket_document
    assert tmpfiles.read_text(encoding="utf-8").splitlines()[-1] == (
        "d /run/sister 0750 root haproxy - -"
    )

    analyzer = shutil.which("systemd-analyze")
    if analyzer:
        result = subprocess.run(
            [analyzer, "security", "--offline=yes", str(service)],
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

        verify = subprocess.run(
            [analyzer, "verify", str(service), str(socket_unit)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
        )
        if verify.returncode != 0:
            lines = [line for line in verify.stdout.splitlines() if line.strip()]
            assert lines and all(
                "Command /opt/sister/build/apps/sisterd/sisterd is not executable" in line
                for line in lines
            ), verify.stdout

    print("sisterd_systemd_unit_tests ok")


if __name__ == "__main__":
    main()
