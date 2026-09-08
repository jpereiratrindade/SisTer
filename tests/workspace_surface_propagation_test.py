#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Hermetic SURFACE -> authenticated workspace regression."""

from __future__ import annotations

import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any


def reserve_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def request(port: int, method: str, path: str, body: Any = None, cookie: str | None = None) -> tuple[int, dict[str, str], bytes]:
    headers = {"Accept": "application/json"}
    if body is not None:
        body = json.dumps(body)
        headers["Content-Type"] = "application/json"
    if cookie:
        headers["Cookie"] = cookie
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    payload = response.read()
    result = response.status, dict(response.getheaders()), payload
    connection.close()
    return result


def wait_for_server(port: int, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("sisterd exited before accepting requests")
        try:
            if request(port, "GET", "/api/health")[0] == 200:
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("sisterd did not become ready")


def run_sisterd_session(executable: str, web_root: str, projection_file: Path) -> tuple[int, subprocess.Popen[str], str, str]:
    """Launches sisterd with the given projection file, registers admin and creates a researcher user.
    Returns (sister_port, process, admin_cookie, researcher_cookie)."""
    sister_port = reserve_port()
    temporary_dir = projection_file.parent
    auth_file = temporary_dir / "auth.tsv"
    semantic_projection_file = temporary_dir / "semantic-projection.tsv"
    semantic_projection_file.write_text("META\tsister.semantic-ecosystem-source/1.0.0\tfixture-r1\n", encoding="utf-8")

    environment = os.environ.copy()
    environment.update({
        "SISTER_ENV": "development",
        "SISTER_BIND_HOST": "127.0.0.1",
        "SISTER_AUTH_FILE": str(auth_file),
        "SISTER_DATABASE_URL": "",
        "SISTER_COOKIE_SECURE": "false",
        "SISTER_ECOSYSTEM_PROJECTION_FILE": str(projection_file),
        "SISTER_SEMANTIC_ECOSYSTEM_PROJECTION_FILE": str(semantic_projection_file),
        "SISTER_SUBSYSTEM_HEALTH_TIMEOUT_MS": "300",
    })

    process = subprocess.Popen(
        [executable, str(sister_port), web_root],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        wait_for_server(sister_port, process)

        status, headers, payload = request(sister_port, "POST", "/api/auth/register", {
            "name": "Ecosystem Admin",
            "email": "ecosystem-admin@test.invalid",
            "password": "ecosystem-test-password-123",
        })
        assert status == 201, (status, payload)
        admin_cookie = headers["Set-Cookie"].split(";", 1)[0]

        status, _, _ = request(sister_port, "POST", "/api/admin/users", {
            "name": "Pesquisador Territorial",
            "email": "pesquisador@test.invalid",
            "password": "pesquisador-password-123",
            "role": "researcher",
        }, admin_cookie)
        assert status == 201, status

        status, headers, _ = request(sister_port, "POST", "/api/auth/login", {
            "email": "pesquisador@test.invalid",
            "password": "pesquisador-password-123",
        })
        assert status == 200, status
        researcher_cookie = headers["Set-Cookie"].split(";", 1)[0]

        return sister_port, process, admin_cookie, researcher_cookie
    except Exception:
        process.terminate()
        process.wait()
        raise


def test_local_surface_projection(executable: str, web_root: str) -> None:
    with tempfile.TemporaryDirectory(prefix="sister-workspace-local-") as temp_dir:
        projection_file = Path(temp_dir) / "projection.tsv"
        projection_file.write_text(
            "META\tneutral-comp\tneutral-lab\tREADY\n"
            "PARTICIPANT\talpha\tsystem_alpha\ttcp\t127.0.0.1\t9101\t/health\n"
            "SURFACE\talpha\talpha-work\tAlpha Work\tExecutar tarefas de pesquisa Alpha\thttp://10.0.0.1:9101/work\tresearch\n"
            "PARTICIPANT\tbeta\tsystem_beta\ttcp\t127.0.0.1\t9102\t/health\n"
            "SURFACE\tbeta\tbeta-dash\tBeta Dashboard\tVisualizar painel analítico Beta\thttp://10.0.0.1:9102/dashboard\tresearch\n"
            "PARTICIPANT\tgamma\tsystem_gamma\ttcp\t127.0.0.1\t9103\t/health\n",
            encoding="utf-8",
        )
        port, proc, admin_cookie, researcher_cookie = run_sisterd_session(executable, web_root, projection_file)
        try:
            for cookie in (researcher_cookie, admin_cookie):
                status, _, payload = request(port, "GET", "/api/v1/workspace", cookie=cookie)
                assert status == 200, (status, payload)
                workspace = json.loads(payload)
                assert workspace["schema"] == "sister.workspace-view/1.0.0"
                surfaces = workspace["surfaces"]
                assert len(surfaces) == 2
                assert surfaces[0] == {
                    "surface_id": "alpha-work",
                    "participant_id": "system_alpha",
                    "label": "Alpha Work",
                    "purpose": "Executar tarefas de pesquisa Alpha",
                    "public_url": "http://10.0.0.1:9101/work",
                    "availability": "available",
                }
                assert surfaces[1] == {
                    "surface_id": "beta-dash",
                    "participant_id": "system_beta",
                    "label": "Beta Dashboard",
                    "purpose": "Visualizar painel analítico Beta",
                    "public_url": "http://10.0.0.1:9102/dashboard",
                    "availability": "available",
                }
                for field in ("runtime", "listen", "port", "probe", "health_path", "deployment"):
                    assert field not in json.dumps(workspace), workspace
        finally:
            proc.terminate()
            proc.wait()


    print("[PASS] Hermetic local SURFACE -> workspace")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: workspace_surface_propagation_test.py <sisterd> <web-root>")
    test_local_surface_projection(sys.argv[1], sys.argv[2])
