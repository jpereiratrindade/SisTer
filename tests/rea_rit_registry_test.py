#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "rea_rit_registry.py"
SCHEMA = ROOT / "contracts" / "rea-rit-registry" / "1.0.0" / "registry.schema.json"
SOURCE_PRINCIPLES = ROOT / "docs" / "rea-rit" / "principios"


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["REARIT_REGISTRY_ROOT"] = str(root)
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_principle(
    principles_dir: Path,
    filename: str,
    *,
    pid: str,
    version: str,
    status: str = "PROPOSTO",
    title: str = "Princípio sintético",
    supersedes: str = "",
    superseded_by: str = "",
) -> Path:
    path = principles_dir / filename
    path.write_text(
        "\n".join(
            [
                f"% REARIT-ID: {pid}",
                f"% REARIT-VERSION: {version}",
                f"% REARIT-STATUS: {status}",
                f"% REARIT-TITLE: {title}",
                "% REARIT-DATE: 2026-08-28",
                "% REARIT-ORIGIN: Teste automatizado",
                f"% REARIT-SUPERSEDES: {supersedes}",
                f"% REARIT-SUPERSEDED-BY: {superseded_by}",
                "",
                rf"\chapter{{{pid} --- {title}}}",
                r"\section{Enunciado normativo}",
                "Conteúdo sintético de teste.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def assert_machine_contract_shape(document: dict, schema: dict) -> None:
    assert schema["properties"]["schema"]["const"] == "sister.rearit.registry/1.0.0"
    assert document["schema"] == schema["properties"]["schema"]["const"]
    assert document["source_of_truth"] == "docs/rea-rit/principios/*.tex"
    assert isinstance(document["principles"], list) and document["principles"]

    required = set(schema["properties"]["principles"]["items"]["required"])
    allowed_status = set(
        schema["properties"]["principles"]["items"]["properties"]["status"]["enum"]
    )

    seen = set()
    for item in document["principles"]:
        assert required.issubset(item.keys())
        assert item["status"] in allowed_status
        assert re.fullmatch(
            r"REARIT-P[0-9]{3}@[0-9]+\.[0-9]+\.[0-9]+",
            item["key"],
        )
        assert item["key"] == f"{item['id']}@{item['version']}"
        assert re.fullmatch(r"[0-9a-f]{64}", item["source_sha256"])
        assert item["key"] not in seen
        seen.add(item["key"])


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sister-rearit-registry-test-") as tmp_text:
        tmp = Path(tmp_text)
        principles_dir = tmp / "docs" / "rea-rit" / "principios"
        principles_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SOURCE_PRINCIPLES, principles_dir)

        index = tmp / "docs" / "rea-rit" / "generated" / "principios_index.tex"
        registry = tmp / "docs" / "rea-rit" / "generated" / "registry.json"

        first = run(tmp, "build")
        assert first.returncode == 0, first.stderr
        assert index.is_file(), "índice derivado ausente após build"
        assert registry.is_file(), "registry.json ausente após build"
        hashes1 = (digest(index), digest(registry))

        second = run(tmp, "build")
        assert second.returncode == 0, second.stderr
        hashes2 = (digest(index), digest(registry))
        assert hashes1 == hashes2, "build derivado não é byte-idempotente"
        print("[PASS] Gate A — build duplo é byte-idempotente para LaTeX e JSON")

        check = run(tmp, "check")
        assert check.returncode == 0, check.stderr
        print("[PASS] Gate B — fontes e artefatos derivados sincronizados")

        listed = run(tmp, "list", "--json")
        assert listed.returncode == 0, listed.stderr
        listed_doc = json.loads(listed.stdout)
        p001 = next(item for item in listed_doc if item["key"] == "REARIT-P001@0.1.0")
        assert p001["status"] == "PROPOSTO"
        assert p001["source"].endswith(
            "principio_manutencao_reflexiva_automatizavel_v0.1.0.tex"
        )
        print("[PASS] Gate C — P001 descoberto por chave histórica")

        registry.write_text(
            registry.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )
        stale = run(tmp, "check")
        assert stale.returncode != 0, "check deveria detectar registry.json adulterado"
        assert "desatualizado" in stale.stderr
        rebuild = run(tmp, "build")
        assert rebuild.returncode == 0, rebuild.stderr
        print("[PASS] Gate D — edição manual do JSON derivado é detectada")

        write_principle(
            principles_dir,
            "principio_sintetico_v0.2.0.tex",
            pid="REARIT-P001",
            version="0.2.0",
            title="Princípio sintético P001 v0.2.0",
            supersedes="REARIT-P001@0.1.0",
        )
        same_lineage = run(tmp, "build")
        assert same_lineage.returncode == 0, same_lineage.stderr
        print("[PASS] Gate E — múltiplas versões do mesmo ID coexistem")

        write_principle(
            principles_dir,
            "duplicata_p001_v0.2.0.tex",
            pid="REARIT-P001",
            version="0.2.0",
            title="Duplicata proibida",
        )
        duplicate = run(tmp, "check")
        assert duplicate.returncode != 0, "chave histórica duplicada deveria falhar"
        assert "chave histórica duplicada" in duplicate.stderr
        (principles_dir / "duplicata_p001_v0.2.0.tex").unlink()
        print("[PASS] Gate F — duplicata de (ID, VERSION) falha fechado")

        write_principle(
            principles_dir,
            "principio_sintetico_v0.10.0.tex",
            pid="REARIT-P001",
            version="0.10.0",
            title="Princípio sintético P001 v0.10.0",
            supersedes="REARIT-P001@0.2.0",
        )
        ordered = run(tmp, "list", "--json")
        assert ordered.returncode == 0, ordered.stderr
        versions = [
            item["version"]
            for item in json.loads(ordered.stdout)
            if item["id"] == "REARIT-P001"
        ]
        assert versions == ["0.1.0", "0.2.0", "0.10.0"], versions
        print("[PASS] Gate G — ordenação usa SemVer numérico, não ordem textual")

        rebuilt = run(tmp, "build")
        assert rebuilt.returncode == 0, rebuilt.stderr
        machine = json.loads(registry.read_text(encoding="utf-8"))
        for item in machine["principles"]:
            source = tmp / item["source"]
            assert hashlib.sha256(source.read_bytes()).hexdigest() == item["source_sha256"]
        print("[PASS] Gate H — source_sha256 ancora cada registro à fonte .tex")

        generator_text = CLI.read_text(encoding="utf-8").lower()
        for concrete in ("nexo", "praxis", "atmos", "urt"):
            assert concrete not in generator_text, (
                f"gerador contém consumidor concreto hardcoded: {concrete}"
            )
        print("[PASS] Gate I — registry permanece neutro de consumidores concretos")

        schema_doc = json.loads(SCHEMA.read_text(encoding="utf-8"))
        assert_machine_contract_shape(machine, schema_doc)
        print("[PASS] Gate J — registry.json satisfaz invariantes do contrato público")

    print("[PASS] REA/RIT Registry Machine Interface v0.1.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
