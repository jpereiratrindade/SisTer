#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts" / "app" / "render-ecosystem-projection.sh"


def main() -> None:
    runtime = (ROOT / "scripts" / "runtime.sh").read_text(encoding="utf-8")
    serve = (ROOT / "scripts" / "app" / "serve.sh").read_text(encoding="utf-8")
    renderer_name = "render-ecosystem-projection.sh"
    assert renderer_name in runtime
    assert renderer_name in serve
    assert '"PARTICIPANT\\t"' not in runtime
    assert '"PARTICIPANT\\t"' not in serve

    resolved = {
        "composition_id": "fixture",
        "deployment_id": "fixture-lab",
        "status": "READY",
        "components": [
            {
                "component_id": "core",
                "system_id": "system_core",
                "runtime": {"transport": "tcp", "listen": "127.0.0.1", "port": 18000},
                "probe": {"health_path": "/health"},
                "gateway": {"host": "core.test", "public_url": "https://core.test"},
            },
            {
                "component_id": "alpha",
                "system_id": "system_alpha",
                "runtime": {"transport": "tcp", "listen": "127.0.0.1", "port": 18001},
                "probe": {"health_path": "/health"},
                "gateway": {"host": "alpha.test", "public_url": "https://alpha.test"},
                "interaction_surfaces": [{
                    "surface_id": "alpha-work",
                    "label": "Alpha",
                    "purpose": "Executar trabalho Alpha",
                    "public_url": "https://alpha.test/work",
                    "access_class": "research",
                }],
            },
        ],
    }

    with tempfile.TemporaryDirectory(prefix="sister-projection-") as temporary:
        source = Path(temporary) / "resolved.json"
        output = Path(temporary) / "projection.tsv"
        source.write_text(json.dumps(resolved), encoding="utf-8")
        subprocess.run([str(RENDERER), str(source), str(output)], check=True)
        lines = output.read_text(encoding="utf-8").splitlines()

    assert lines[0] == "META\tfixture\tfixture-lab\tREADY"
    assert [line.split("\t", 2)[:2] for line in lines[1:]] == [
        ["PARTICIPANT", "core"],
        ["PARTICIPANT", "alpha"],
        ["SURFACE", "alpha"],
    ]
    assert lines[-1] == (
        "SURFACE\talpha\talpha-work\tAlpha\tExecutar trabalho Alpha\t"
        "https://alpha.test/work\tresearch"
    )
    print("ecosystem_projection_renderer_test ok")


if __name__ == "__main__":
    main()
