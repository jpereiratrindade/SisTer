#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validador e gerador do Registro Evolutivo de Princípios REA/RIT."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(
    os.environ.get(
        "REARIT_REGISTRY_ROOT",
        str(Path(__file__).resolve().parents[1]),
    )
).expanduser().resolve()

PRINCIPLES_DIR = ROOT / "docs" / "rea-rit" / "principios"
GENERATED_DIR = ROOT / "docs" / "rea-rit" / "generated"
GENERATED_INDEX = GENERATED_DIR / "principios_index.tex"
GENERATED_REGISTRY = GENERATED_DIR / "registry.json"

REGISTRY_SCHEMA = "sister.rearit.registry/1.0.0"
SOURCE_OF_TRUTH = "docs/rea-rit/principios/*.tex"

META_KEYS = (
    "ID",
    "VERSION",
    "STATUS",
    "TITLE",
    "DATE",
    "ORIGIN",
    "SUPERSEDES",
    "SUPERSEDED-BY",
)
ALLOWED_STATUS = {"PROPOSTO", "ACEITO", "REVISADO", "DEPRECIADO", "SUPERSEDIDO"}
ID_RE = re.compile(r"^REARIT-P([0-9]{3})$")
VERSION_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
REFERENCE_RE = re.compile(
    r"^REARIT-P[0-9]{3}@(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
FILE_VERSION_RE = re.compile(r"_v([0-9]+\.[0-9]+\.[0-9]+)\.tex$")
META_RE = re.compile(r"^%\s*REARIT-([A-Z-]+):\s*(.*)\s*$")


class RegistryError(RuntimeError):
    pass


def relpath(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def semver_tuple(version: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(version)
    if not match:
        raise RegistryError(f"versão semântica inválida: {version}")
    return tuple(int(part) for part in match.groups())


@dataclass(frozen=True)
class Principle:
    path: Path
    principle_id: str
    version: str
    status: str
    title: str
    date: str
    origin: str
    supersedes: str
    superseded_by: str

    @property
    def ordinal(self) -> int:
        match = ID_RE.fullmatch(self.principle_id)
        assert match is not None
        return int(match.group(1))

    @property
    def key(self) -> str:
        return f"{self.principle_id}@{self.version}"

    @property
    def version_key(self) -> tuple[int, int, int]:
        return semver_tuple(self.version)

    @property
    def source(self) -> str:
        return relpath(self.path)

    @property
    def source_sha256(self) -> str:
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "id": self.principle_id,
            "version": self.version,
            "status": self.status,
            "title": self.title,
            "date": self.date,
            "origin": self.origin,
            "supersedes": self.supersedes or None,
            "superseded_by": self.superseded_by or None,
            "source": self.source,
            "source_sha256": self.source_sha256,
        }


def parse_principle(path: Path) -> Principle:
    metadata: dict[str, str] = {}
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines()[:40]:
        match = META_RE.match(line)
        if match:
            metadata[match.group(1)] = match.group(2).strip()

    missing = [key for key in META_KEYS if key not in metadata]
    if missing:
        raise RegistryError(
            f"{relpath(path)}: metadados ausentes: {', '.join(missing)}"
        )

    pid = metadata["ID"]
    version = metadata["VERSION"]
    status = metadata["STATUS"]

    if not ID_RE.fullmatch(pid):
        raise RegistryError(f"{relpath(path)}: REARIT-ID inválido: {pid}")
    if not VERSION_RE.fullmatch(version):
        raise RegistryError(f"{relpath(path)}: REARIT-VERSION inválida: {version}")
    if status not in ALLOWED_STATUS:
        raise RegistryError(f"{relpath(path)}: status inválido: {status}")

    file_match = FILE_VERSION_RE.search(path.name)
    if not file_match:
        raise RegistryError(
            f"{relpath(path)}: filename deve terminar em _vMAJOR.MINOR.PATCH.tex"
        )
    if file_match.group(1) != version:
        raise RegistryError(
            f"{relpath(path)}: versão do filename ({file_match.group(1)}) "
            f"diverge do metadado ({version})"
        )

    if not metadata["TITLE"]:
        raise RegistryError(f"{relpath(path)}: título vazio")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", metadata["DATE"]):
        raise RegistryError(f"{relpath(path)}: data deve usar YYYY-MM-DD")
    if not metadata["ORIGIN"]:
        raise RegistryError(f"{relpath(path)}: origem vazia")

    for relation_name in ("SUPERSEDES", "SUPERSEDED-BY"):
        relation = metadata[relation_name]
        if relation and not REFERENCE_RE.fullmatch(relation):
            raise RegistryError(
                f"{relpath(path)}: {relation_name} deve usar "
                "REARIT-Pxxx@MAJOR.MINOR.PATCH"
            )

    if metadata["SUPERSEDED-BY"] and status != "SUPERSEDIDO":
        raise RegistryError(
            f"{relpath(path)}: SUPERSEDED-BY exige status SUPERSEDIDO"
        )

    return Principle(
        path=path,
        principle_id=pid,
        version=version,
        status=status,
        title=metadata["TITLE"],
        date=metadata["DATE"],
        origin=metadata["ORIGIN"],
        supersedes=metadata["SUPERSEDES"],
        superseded_by=metadata["SUPERSEDED-BY"],
    )


def load_registry() -> list[Principle]:
    if not PRINCIPLES_DIR.is_dir():
        raise RegistryError(
            f"diretório de princípios ausente: {relpath(PRINCIPLES_DIR)}"
        )

    paths = sorted(PRINCIPLES_DIR.glob("*.tex"))
    if not paths:
        raise RegistryError("nenhum princípio REA/RIT encontrado")

    principles = [parse_principle(path) for path in paths]

    seen_keys: dict[tuple[str, str], Path] = {}
    for item in principles:
        identity = (item.principle_id, item.version)
        if identity in seen_keys:
            raise RegistryError(
                f"chave histórica duplicada {item.key}: "
                f"{relpath(seen_keys[identity])} e {relpath(item.path)}"
            )
        seen_keys[identity] = item.path

    known_refs = {item.key for item in principles}
    for item in principles:
        for relation_name, relation_value in (
            ("SUPERSEDES", item.supersedes),
            ("SUPERSEDED-BY", item.superseded_by),
        ):
            if relation_value and relation_value not in known_refs:
                raise RegistryError(
                    f"{relpath(item.path)}: {relation_name} referencia "
                    f"chave histórica desconhecida: {relation_value}"
                )
            if relation_value == item.key:
                raise RegistryError(
                    f"{relpath(item.path)}: {relation_name} não pode "
                    "referenciar a própria versão"
                )

    return sorted(
        principles,
        key=lambda p: (p.ordinal, p.version_key, p.path.name),
    )


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def build_index(principles: list[Principle]) -> str:
    lines = [
        "% AUTO-GENERATED by scripts/rea_rit_registry.py -- DO NOT EDIT",
        "% Source of truth: docs/rea-rit/principios/*.tex",
        "",
        r"\chapter*{Catálogo de princípios}",
        r"\addcontentsline{toc}{chapter}{Catálogo de princípios}",
        "",
        r"\begin{description}[style=nextline]",
    ]
    for p in principles:
        label = latex_escape(f"{p.principle_id} v{p.version} [{p.status}]")
        detail = latex_escape(f"{p.title} — origem: {p.origin}; data: {p.date}.")
        lines.append(rf"  \item[\texttt{{{label}}}] {detail}")
    lines.extend([r"\end{description}", ""])

    for p in principles:
        rel = p.path.relative_to(ROOT / "docs" / "rea-rit")
        lines.append(rf"\input{{{rel.as_posix()}}}")
        lines.append("")
    return "\n".join(lines)


def build_machine_registry(principles: list[Principle]) -> str:
    document = {
        "schema": REGISTRY_SCHEMA,
        "source_of_truth": SOURCE_OF_TRUTH,
        "principles": [p.as_dict() for p in principles],
    }
    return json.dumps(
        document,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"


def atomic_write_if_changed(path: Path, content: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()
    return True


def cmd_check() -> int:
    principles = load_registry()

    expected_index = build_index(principles)
    expected_registry = build_machine_registry(principles)

    missing: list[str] = []
    stale: list[str] = []

    for path, expected in (
        (GENERATED_INDEX, expected_index),
        (GENERATED_REGISTRY, expected_registry),
    ):
        if not path.exists():
            missing.append(relpath(path))
        elif path.read_text(encoding="utf-8") != expected:
            stale.append(relpath(path))

    if stale:
        raise RegistryError(
            "artefato(s) derivado(s) desatualizado(s): "
            + ", ".join(stale)
            + "; execute `python3 scripts/rea_rit_registry.py build`"
        )

    print(f"[PASS] {len(principles)} versão(ões) de princípio REA/RIT válida(s)")
    print("[PASS] chaves históricas, versões, estados e genealogia consistentes")

    if missing:
        print(
            "[INFO] artefato(s) derivado(s) ainda ausente(s): "
            + ", ".join(missing)
            + "; execute build"
        )
    else:
        print("[PASS] índice LaTeX e registry.json sincronizados")

    return 0


def cmd_build() -> int:
    principles = load_registry()
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    index_changed = atomic_write_if_changed(
        GENERATED_INDEX,
        build_index(principles),
    )
    registry_changed = atomic_write_if_changed(
        GENERATED_REGISTRY,
        build_machine_registry(principles),
    )

    if index_changed:
        print(f"[PASS] índice REA/RIT atualizado: {relpath(GENERATED_INDEX)}")
    else:
        print("[PASS] índice REA/RIT já estava convergido")

    if registry_changed:
        print(f"[PASS] registry REA/RIT atualizado: {relpath(GENERATED_REGISTRY)}")
    else:
        print("[PASS] registry REA/RIT já estava convergido")

    return 0


def cmd_list(as_json: bool) -> int:
    principles = load_registry()
    if as_json:
        print(
            json.dumps(
                [p.as_dict() for p in principles],
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    else:
        for p in principles:
            print(
                f"{p.principle_id}\t{p.version}\t{p.status}\t"
                f"{p.title}\t{p.source}"
            )
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Valida e deriva o Registro Evolutivo de Princípios REA/RIT"
    )
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "check",
        help="valida fontes e sincronização dos artefatos derivados",
    )
    sub.add_parser(
        "build",
        help="gera deterministicamente índice LaTeX e registry.json",
    )
    lp = sub.add_parser("list", help="lista versões de princípios")
    lp.add_argument("--json", action="store_true", help="emite JSON")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "check":
            return cmd_check()
        if args.command == "build":
            return cmd_build()
        if args.command == "list":
            return cmd_list(args.json)
        raise RegistryError(f"comando desconhecido: {args.command}")
    except (RegistryError, OSError, UnicodeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
