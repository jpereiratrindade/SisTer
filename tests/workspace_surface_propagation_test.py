#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""End-to-end test proving participant-neutral surface discovery:
1. Generic neutral test (alpha, beta, gamma): descriptor.path -> resolved public_url -> projection SURFACE -> workspace
2. Real Atmos witness test: sister-atmos/.sister/component.json -> validation -> resolution -> projection -> GET /api/v1/workspace
"""

from __future__ import annotations

import copy
import http.client
from importlib.machinery import SourceFileLoader
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


def test_generic_fixture_surface_propagation(root_dir: Path, executable: str, web_root: str) -> None:
    """GENERIC TEST:
    Neutral fixture: alpha, beta, gamma with at least two different surfaces.
    Proves: descriptor.path -> resolved public_url -> projection SURFACE -> workspace
    without identity rules.
    """
    infra_dir = root_dir.parent / "sister-infra"
    deployment_cli = infra_dir / "bin" / "sister-deployment"
    renderer_sh = root_dir / "scripts" / "app" / "render-ecosystem-projection.sh"

    with tempfile.TemporaryDirectory(prefix="sister-generic-test-") as temp_dir:
        temp_path = Path(temp_dir)

        # 1. Neutral candidate descriptor with alpha (surface /work), beta (surface /dashboard), gamma (no surface)
        candidate_manifest = {
            "schema": "sister.infra.workstation.candidate/1",
            "candidate_id": "wc-neutral-fixture",
            "composition": {"composition_id": "neutral-comp"},
            "qualification": {"status": "PASS"},
            "deployment": {"status": "PENDING_BINDINGS"},
            "components": [
                {
                    "component_id": "alpha",
                    "system_id": "system_alpha",
                    "path": "components/alpha",
                    "interaction_surfaces": [
                        {
                            "surface_id": "alpha-work",
                            "label": "Alpha Work",
                            "purpose": "Executar tarefas de pesquisa Alpha",
                            "path": "/work",
                            "access_class": "research",
                        }
                    ],
                },
                {
                    "component_id": "beta",
                    "system_id": "system_beta",
                    "path": "components/beta",
                    "interaction_surfaces": [
                        {
                            "surface_id": "beta-dash",
                            "label": "Beta Dashboard",
                            "purpose": "Visualizar painel analítico Beta",
                            "path": "/dashboard",
                            "access_class": "research",
                        }
                    ],
                },
                {
                    "component_id": "gamma",
                    "system_id": "system_gamma",
                    "path": "components/gamma",
                },
            ],
        }

        deployment_doc = {
            "schema": "sister.infra.deployment/1.0.0",
            "deployment_id": "neutral-lab",
            "composition_id": "neutral-comp",
            "gateway": {
                "protocol": "http",
                "listen": "10.0.0.1",
                "exposure": "ip-ports",
            },
            "bindings": [
                {
                    "system_id": "system_alpha",
                    "runtime": {"transport": "tcp", "listen": "127.0.0.1", "port": 9101},
                    "probe": {"health_path": "/health"},
                },
                {
                    "system_id": "system_beta",
                    "runtime": {"transport": "tcp", "listen": "127.0.0.1", "port": 9102},
                    "probe": {"health_path": "/health"},
                },
                {
                    "system_id": "system_gamma",
                    "runtime": {"transport": "tcp", "listen": "127.0.0.1", "port": 9103},
                    "probe": {"health_path": "/health"},
                },
            ],
        }

        cand_file = temp_path / "candidate.json"
        cand_file.write_text(json.dumps(candidate_manifest), encoding="utf-8")
        dep_file = temp_path / "deployment.json"
        dep_file.write_text(json.dumps(deployment_doc), encoding="utf-8")

        # 2. Resolve deployment: descriptor.path -> resolved public_url
        res_cmd = subprocess.run(
            [sys.executable, str(deployment_cli), "resolve", str(cand_file), str(dep_file), "--json"],
            text=True,
            capture_output=True,
            check=True,
        )
        resolved = json.loads(res_cmd.stdout)
        assert resolved["schema"] == "sister.infra.deployment.resolved/1"

        resolved_surfaces = {c["component_id"]: c.get("interaction_surfaces", []) for c in resolved["components"]}
        assert len(resolved_surfaces["alpha"]) == 1
        assert resolved_surfaces["alpha"][0]["public_url"] == "http://10.0.0.1:9101/work"
        assert len(resolved_surfaces["beta"]) == 1
        assert resolved_surfaces["beta"][0]["public_url"] == "http://10.0.0.1:9102/dashboard"
        assert "interaction_surfaces" not in resolved["components"][2]

        resolved_file = temp_path / "resolved.json"
        resolved_file.write_text(json.dumps(resolved), encoding="utf-8")

        # 3. Render ecosystem projection: resolved public_url -> projection SURFACE
        projection_file = temp_path / "projection.tsv"
        subprocess.run([str(renderer_sh), str(resolved_file), str(projection_file)], check=True)
        tsv_content = projection_file.read_text(encoding="utf-8")
        tsv_lines = [line.split("\t") for line in tsv_content.splitlines()]

        surface_rows = [row for row in tsv_lines if row[0] == "SURFACE"]
        assert len(surface_rows) == 2
        assert surface_rows[0] == [
            "SURFACE", "alpha", "alpha-work", "Alpha Work",
            "Executar tarefas de pesquisa Alpha", "http://10.0.0.1:9101/work", "research"
        ]
        assert surface_rows[1] == [
            "SURFACE", "beta", "beta-dash", "Beta Dashboard",
            "Visualizar painel analítico Beta", "http://10.0.0.1:9102/dashboard", "research"
        ]

        # Also verify that sister-reconcile's Python renderer matches
        reconcile_mod = SourceFileLoader("sister_reconcile", str(infra_dir / "bin" / "sister-reconcile")).load_module()
        py_rendered = reconcile_mod.render_ecosystem_projection(resolved)
        assert "SURFACE\talpha\talpha-work\tAlpha Work\tExecutar tarefas de pesquisa Alpha\thttp://10.0.0.1:9101/work\tresearch" in py_rendered
        assert "SURFACE\tbeta\tbeta-dash\tBeta Dashboard\tVisualizar painel analítico Beta\thttp://10.0.0.1:9102/dashboard\tresearch" in py_rendered
        assert "gamma" not in [r[1] for r in [line.split("\t") for line in py_rendered.splitlines() if line.startswith("SURFACE")]]

        # 4. Sister consumption: projection SURFACE -> workspace
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
        finally:
            proc.terminate()
            proc.wait()

    print("[PASS] Generic neutral surface propagation test: descriptor -> resolved -> SURFACE -> workspace")


def test_real_atmos_witness(root_dir: Path, executable: str, web_root: str) -> None:
    """REAL ATMOS WITNESS:
    Proves:
      sister-atmos/.sister/component.json
          ↓
      sister-component validation/qualification
          ↓
      composition/deployment resolution
          ↓
      rendered ecosystem projection
          ↓
      GET /api/v1/workspace
          ↓
      Atmos presente com URL navegável correta
    """
    dev_dir = root_dir.parent
    atmos_dir = dev_dir / "sister-atmos"
    infra_dir = dev_dir / "sister-infra"
    component_cli = infra_dir / "bin" / "sister-component"
    composition_cli = infra_dir / "bin" / "sister-composition"
    deployment_cli = infra_dir / "bin" / "sister-deployment"
    renderer_sh = root_dir / "scripts" / "app" / "render-ecosystem-projection.sh"

    # Step 1: Validate descriptor of sister-atmos
    res_validate = subprocess.run(
        [sys.executable, str(component_cli), "validate", str(atmos_dir)],
        text=True,
        capture_output=True,
        check=True,
    )
    assert "[PASS] atmos atende sister.component/1.0.0" in res_validate.stdout

    # Step 2: Read real descriptor and assert declared surface
    descriptor_path = atmos_dir / ".sister" / "component.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    assert descriptor["component_id"] == "atmos"
    assert descriptor["system_id"] == "sister_atmos"
    assert descriptor["interaction_surfaces"] == [
        {
            "surface_id": "atmos-precipitation",
            "label": "Atmos",
            "purpose": "Consultar e comparar precipitação em contexto territorial",
            "path": "/",
            "access_class": "research",
        }
    ]

    with tempfile.TemporaryDirectory(prefix="sister-atmos-witness-") as temp_dir:
        temp_path = Path(temp_dir)

        # Step 3: Resolve real composition (workstation.json)
        workstation_comp = infra_dir / "config" / "compositions" / "workstation.json"
        res_comp = subprocess.run(
            [sys.executable, str(composition_cli), "resolve", str(workstation_comp), "--json"],
            text=True,
            capture_output=True,
            check=True,
        )
        resolved_comp = json.loads(res_comp.stdout)
        atmos_comp = next(c for c in resolved_comp["components"] if c["component_id"] == "atmos")
        assert atmos_comp["interaction_surfaces"] == descriptor["interaction_surfaces"]

        # Step 4: Resolve deployment (workstation-lab.json)
        # Construct candidate manifest from resolved composition for the deployment resolver
        workstation_dep = infra_dir / "config" / "deployments" / "workstation-lab.json"
        candidate_manifest = {
            "schema": "sister.infra.workstation.candidate/1",
            "candidate_id": "wc-witness-candidate",
            "composition": {"composition_id": "workstation"},
            "qualification": {"status": "PASS"},
            "deployment": {"status": "PENDING_BINDINGS"},
            "components": [
                {
                    "component_id": c["component_id"],
                    "system_id": c["system_id"],
                    "path": f"components/{c['component_id']}",
                    "interaction_surfaces": c.get("interaction_surfaces", []),
                }
                for c in resolved_comp["components"]
            ],
        }
        cand_file = temp_path / "candidate.json"
        cand_file.write_text(json.dumps(candidate_manifest), encoding="utf-8")

        res_dep = subprocess.run(
            [sys.executable, str(deployment_cli), "resolve", str(cand_file), str(workstation_dep), "--json"],
            text=True,
            capture_output=True,
            check=True,
        )
        resolved_dep = json.loads(res_dep.stdout)
        resolved_dep_file = temp_path / "resolved.json"
        resolved_dep_file.write_text(json.dumps(resolved_dep), encoding="utf-8")

        atmos_resolved = next(c for c in resolved_dep["components"] if c["component_id"] == "atmos")
        assert atmos_resolved["interaction_surfaces"] == [
            {
                "surface_id": "atmos-precipitation",
                "label": "Atmos",
                "purpose": "Consultar e comparar precipitação em contexto territorial",
                "access_class": "research",
                "public_url": "http://10.163.80.176:8095",
            }
        ]

        # Step 5: Render ecosystem projection
        projection_file = temp_path / "ecosystem_projection.tsv"
        subprocess.run([str(renderer_sh), str(resolved_dep_file), str(projection_file)], check=True)
        tsv_content = projection_file.read_text(encoding="utf-8")
        tsv_lines = [line.split("\t") for line in tsv_content.splitlines()]

        surfaces_in_tsv = [row for row in tsv_lines if row[0] == "SURFACE"]
        surface_cids = [s[1] for s in surfaces_in_tsv]

        # Nexo, URT, and Atmos declared surfaces; SisTer (host) and Praxis (headless) did not
        assert "atmos" in surface_cids
        assert "nexo" in surface_cids
        assert "urt" in surface_cids
        assert "sister" not in surface_cids
        assert "praxis" not in surface_cids

        atmos_row = next(s for s in surfaces_in_tsv if s[1] == "atmos")
        assert atmos_row == [
            "SURFACE", "atmos", "atmos-precipitation", "Atmos",
            "Consultar e comparar precipitação em contexto territorial",
            "http://10.163.80.176:8095", "research"
        ]

        # Step 6: Start sisterd and query GET /api/v1/workspace
        port, proc, admin_cookie, researcher_cookie = run_sisterd_session(executable, web_root, projection_file)
        try:
            for cookie in (researcher_cookie, admin_cookie):
                status, _, payload = request(port, "GET", "/api/v1/workspace", cookie=cookie)
                assert status == 200, (status, payload)
                workspace = json.loads(payload)
                assert workspace["schema"] == "sister.workspace-view/1.0.0"

                workspace_surfaces = workspace["surfaces"]
                surface_ids = [s["surface_id"] for s in workspace_surfaces]

                # Factual verification: Nexo, URT, Atmos present
                assert surface_ids == ["nexo-research", "urt-registry", "atmos-precipitation"]

                atmos_surface = next(s for s in workspace_surfaces if s["surface_id"] == "atmos-precipitation")
                assert atmos_surface == {
                    "surface_id": "atmos-precipitation",
                    "participant_id": "sister_atmos",
                    "label": "Atmos",
                    "purpose": "Consultar e comparar precipitação em contexto territorial",
                    "public_url": "http://10.163.80.176:8095",
                    "availability": "available",
                }

                # Prove SisTer and Praxis do not appear as surfaces
                participant_ids = [s["participant_id"] for s in workspace_surfaces]
                assert "sister" not in participant_ids
                assert "sister_praxis" not in participant_ids

                # Prove internal operational details are NOT leaked to workspace
                serialized = json.dumps(workspace)
                for secret_or_internal in ("listen", "health_path", "port", "deployment_status"):
                    assert secret_or_internal not in serialized, f"internal field '{secret_or_internal}' found in workspace payload"
        finally:
            proc.terminate()
            proc.wait()

    print("[PASS] Real Atmos witness test: sister-atmos -> validation -> resolution -> projection -> workspace (Atmos navigable)")


def main() -> None:
    if len(sys.argv) < 3:
        print(f"Uso: {sys.argv[0]} <sisterd-executable> <web-root>", file=sys.stderr)
        sys.exit(2)

    executable = sys.argv[1]
    web_root = sys.argv[2]
    root_dir = Path(__file__).resolve().parents[1]

    test_generic_fixture_surface_propagation(root_dir, executable, web_root)
    test_real_atmos_witness(root_dir, executable, web_root)
    print("\n[ALL PASS] All workspace surface propagation and witness tests succeeded.")


if __name__ == "__main__":
    main()
