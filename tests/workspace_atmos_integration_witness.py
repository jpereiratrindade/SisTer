#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit multi-repository witness; deliberately outside component CTest."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from workspace_surface_propagation_test import request, run_sisterd_session

def test_real_atmos_witness(root_dir: Path, infra_dir: Path, atmos_dir: Path, executable: str, web_root: str) -> None:
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sister-root", type=Path, required=True)
    parser.add_argument("--infra-root", type=Path, required=True)
    parser.add_argument("--atmos-root", type=Path, required=True)
    parser.add_argument("--sisterd", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.sister_root / "web", args.infra_root / "bin/sister-deployment",
                 args.atmos_root / ".sister/component.json", args.sisterd):
        if not path.exists():
            parser.error(f"required witness dependency missing: {path}")
    test_real_atmos_witness(args.sister_root.resolve(), args.infra_root.resolve(),
                            args.atmos_root.resolve(), str(args.sisterd.resolve()),
                            str(args.sister_root.resolve() / "web"))


if __name__ == "__main__":
    main()
