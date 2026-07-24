#!/usr/bin/env python3
"""Ensure that governed local SisTer subsystems are running."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEV_ROOT = ROOT.parents[1]
REGISTRY = ROOT / "config" / "local_resources.json"
RUN_DIR = ROOT / ".run" / "subsystems"


def log(message: str) -> None:
    print(f"[subsistemas] {message}", flush=True)


def governed_projects(environment: str) -> list[dict[str, Any]]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return [
        project
        for project in data["projects"]
        if project.get("integrates_with_sister")
        and project.get("orchestration", {}).get("policy") == "ensure-running"
        and project["orchestration"].get("environment") == environment
    ]


def repository_path(project: dict[str, Any]) -> Path:
    path = (DEV_ROOT / project["repository"]).resolve()
    path.relative_to(DEV_ROOT.resolve())
    if not path.is_dir():
        raise RuntimeError(f"repositório ausente: {path}")
    return path


def start_argv(project: dict[str, Any], repository: Path) -> list[str]:
    argv = project["orchestration"]["start"]["argv"]
    entrypoint = argv[0]
    if not entrypoint.startswith("./") or ".." in Path(entrypoint).parts:
        raise RuntimeError("o executável deve ser um caminho relativo governado")
    executable = (repository / entrypoint).resolve()
    executable.relative_to(repository)
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise RuntimeError(f"executável ausente ou sem permissão: {executable}")
    return argv


def healthy(project: dict[str, Any]) -> bool:
    health = project["orchestration"]["health"]
    context = None
    if health["url"].startswith("https://") and not health.get("tls_verify", True):
        context = ssl._create_unverified_context()
    request = Request(health["url"], headers={"User-Agent": "SisTer-Orchestrator/1.0"})
    try:
        with urlopen(request, timeout=3, context=context) as response:
            return response.status < 500
    except HTTPError as error:
        return error.code < 500
    except (OSError, URLError, TimeoutError):
        return False


def start_project(project: dict[str, Any]) -> tuple[bool, str]:
    project_id = project["id"]
    orchestration = project["orchestration"]
    repository = repository_path(project)
    argv = start_argv(project, repository)
    environment = os.environ.copy()
    environment["SISTER_HOME"] = str(ROOT)
    environment.update(orchestration["start"].get("environment", {}))

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    log_path = RUN_DIR / f"{project_id}.log"
    pid_path = RUN_DIR / f"{project_id}.pid"
    with log_path.open("ab", buffering=0) as output:
        output.write(
            f"\n[{time.strftime('%Y-%m-%dT%H:%M:%S%z')}] iniciando {project_id}\n".encode()
        )
        process = subprocess.Popen(
            argv,
            cwd=repository,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    pid_path.write_text(f"{process.pid}\n", encoding="utf-8")

    deadline = time.monotonic() + orchestration["start"]["ready_timeout_seconds"]
    while time.monotonic() < deadline:
        if healthy(project):
            if process.poll() is not None:
                pid_path.unlink(missing_ok=True)
            return True, f"iniciado; log {log_path}"
        return_code = process.poll()
        if return_code not in (None, 0):
            pid_path.unlink(missing_ok=True)
            return False, f"inicialização terminou com código {return_code}; log {log_path}"
        time.sleep(1)

    if process.poll() is not None:
        pid_path.unlink(missing_ok=True)
    return False, f"não ficou saudável dentro do prazo; log {log_path}"


def ensure(environment: str, selected: set[str], strict: bool) -> int:
    projects = governed_projects(environment)
    if selected:
        projects = [project for project in projects if project["id"] in selected]
        missing = selected - {project["id"] for project in projects}
        if missing:
            raise RuntimeError(f"projetos não governados para {environment}: {', '.join(sorted(missing))}")
    if not projects:
        log(f"nenhum subsistema governado para o ambiente {environment}")
        return 0

    failures: list[tuple[str, bool]] = []
    for project in projects:
        project_id = project["id"]
        if healthy(project):
            log(f"{project_id}: saudável")
            continue
        log(f"{project_id}: indisponível; iniciando pelo contrato local")
        try:
            success, detail = start_project(project)
        except (OSError, RuntimeError, ValueError) as error:
            success, detail = False, str(error)
        log(f"{project_id}: {'saudável' if success else 'falhou'} — {detail}")
        if not success:
            failures.append((project_id, project["orchestration"]["required"]))

    required_failures = [project_id for project_id, required in failures if required]
    if failures:
        log("degradação: " + ", ".join(project_id for project_id, _ in failures))
    if strict and failures:
        return 1
    return 1 if required_failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", default="dev")
    parser.add_argument("--project", action="append", default=[])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="valida e lista a seleção sem consultar nem iniciar serviços",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    projects = governed_projects(args.environment)
    selected = set(args.project)
    if selected:
        projects = [project for project in projects if project["id"] in selected]
    for project in projects:
        repository = repository_path(project)
        start_argv(project, repository)
    if args.check:
        log(
            f"configuração válida para {len(projects)} subsistema(s): "
            + ", ".join(project["id"] for project in projects)
        )
        return 0

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    with (RUN_DIR / "ensure.lock").open("w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return ensure(args.environment, selected, args.strict)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, TypeError, ValueError, RuntimeError) as error:
        print(f"[subsistemas] erro de configuração: {error}", file=sys.stderr)
        raise SystemExit(2)
