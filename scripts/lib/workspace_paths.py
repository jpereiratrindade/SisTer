#!/usr/bin/env python3
"""Governed repository path resolution for SisTer and local subsystems."""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Any


def project_root_from_script(path: Path) -> Path:
    return path.resolve().parents[1]


def default_workspace_root(root: Path) -> Path:
    resolved = root.resolve()
    try:
        return resolved.parents[1]
    except IndexError as error:
        raise RuntimeError(f"cannot derive workspace root from {resolved}") from error


def workspace_root(root: Path) -> Path:
    configured = os.environ.get("SISTER_WORKSPACE_ROOT")
    path = Path(configured).expanduser() if configured else default_workspace_root(root)
    resolved = path.resolve()
    if not resolved.is_dir():
        raise RuntimeError(f"workspace root is absent: {resolved}")
    return resolved


def repository_env_name(project_id: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", project_id).upper().strip("_")
    if not normalized:
        raise RuntimeError("project id cannot be converted to an environment name")
    return f"SISTER_REPOSITORY_ROOT_{normalized}"


def integration_identifier(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    patterns = [
        r"Identificador(?:\s+deste\s+projeto)?\s+no\s+registro(?:\s+central)?\s*:\s*`([^`]+)`",
        r"Identificador\s+no\s+registro\s*:\s*`([^`]+)`",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def integration_contracts(root: Path, max_depth: int = 4) -> dict[str, list[Path]]:
    workspace = workspace_root(root)
    ignored = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".run",
        ".venv",
        "__pycache__",
        "build",
        "data",
        "node_modules",
        "postgres-data",
        "storage",
        "var",
        "venv",
    }
    contracts: dict[str, list[Path]] = {}
    for directory, names, files in os.walk(workspace, onerror=lambda _error: None):
        current = Path(directory)
        try:
            depth = len(current.relative_to(workspace).parts)
        except ValueError:
            depth = max_depth
        names[:] = [
            name for name in names
            if name not in ignored and not name.startswith(".")
        ]
        if depth >= max_depth:
            names[:] = []
        if "SISTER_INTEGRATION.md" not in files:
            continue
        identifier = integration_identifier(current / "SISTER_INTEGRATION.md")
        if identifier:
            contracts.setdefault(identifier, []).append(current.resolve())
    return contracts


def discover_repository(root: Path, project_id: str) -> Path | None:
    matches = integration_contracts(root).get(project_id, [])
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        formatted = ", ".join(str(path) for path in sorted(matches))
        raise RuntimeError(f"multiple contract repositories found for {project_id}: {formatted}")
    return None


def repository_path(root: Path, project: dict[str, Any]) -> Path:
    project_id = project.get("id")
    if not isinstance(project_id, str) or not project_id:
        raise RuntimeError("project id is missing")
    repository = project.get("repository")
    if not isinstance(repository, str) or not repository:
        raise RuntimeError(f"project {project_id} has no repository")

    override = os.environ.get(repository_env_name(project_id))
    if override:
        path = Path(override).expanduser()
    else:
        pure = Path(repository)
        if pure.is_absolute() or ".." in pure.parts:
            raise RuntimeError(f"repository path is not governed in {project_id}")
        path = workspace_root(root) / pure

    resolved = path.resolve()
    if not resolved.is_dir() and not override:
        discovered = discover_repository(root, project_id)
        if discovered is not None:
            return discovered
    if not resolved.is_dir():
        env_name = repository_env_name(project_id)
        raise RuntimeError(
            f"repository is absent for {project_id}: {resolved}. "
            f"Informe o caminho com {env_name}=/caminho/do/repositorio "
            f"ou ajuste SISTER_WORKSPACE_ROOT."
        )
    return resolved


def describe_path_controls(root: Path) -> dict[str, str]:
    return {
        "workspace_root": str(workspace_root(root)),
        "workspace_env": "SISTER_WORKSPACE_ROOT",
        "repository_override_prefix": "SISTER_REPOSITORY_ROOT_",
    }
