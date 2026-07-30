#!/usr/bin/env python3
"""Ensure that governed local SisTer subsystems are running."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEV_ROOT = ROOT.parents[1]
REGISTRY = ROOT / "config" / "local_resources.json"
RUN_DIR = ROOT / ".run" / "subsystems"


@dataclass(frozen=True)
class HealthResult:
    state: str
    detail: str


def log(message: str) -> None:
    print(f"[subsistemas] {message}", flush=True)


def governed_projects(environment: str) -> list[dict[str, Any]]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return [
        project
        for project in data["projects"]
        if (project.get("integrates_with_sister") or project.get("integrates_with"))
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


def source_digest(project: dict[str, Any], repository: Path) -> str | None:
    refresh = project["orchestration"].get("refresh")
    if refresh is None:
        return None
    digest = hashlib.sha256()
    for configured_path in refresh["paths"]:
        source = (repository / configured_path).resolve()
        source.relative_to(repository)
        if not source.exists():
            raise RuntimeError(f"fonte monitorada ausente: {source}")
        files = [source] if source.is_file() else sorted(
            path for path in source.rglob("*") if path.is_file()
        )
        for path in files:
            relative = path.relative_to(repository).as_posix().encode()
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def recorded_digest(project_id: str) -> str | None:
    path = RUN_DIR / f"{project_id}.source.sha256"
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except FileNotFoundError:
        return None


def record_digest(project_id: str, digest: str | None) -> None:
    if digest is not None:
        (RUN_DIR / f"{project_id}.source.sha256").write_text(
            f"{digest}\n", encoding="utf-8"
        )


def health_result(project: dict[str, Any]) -> HealthResult:
    health = project["orchestration"]["health"]
    endpoint = urlparse(health["url"])
    try:
        with socket.create_connection((endpoint.hostname, endpoint.port), timeout=1):
            pass
    except OSError as error:
        return HealthResult("unavailable", str(error))

    context = None
    if health["url"].startswith("https://") and not health.get("tls_verify", True):
        context = ssl._create_unverified_context()
    request = Request(health["url"], headers={"User-Agent": "SisTer-Orchestrator/1.0"})
    handlers: list[Any] = [ProxyHandler({})]
    if context is not None:
        handlers.append(HTTPSHandler(context=context))
    opener = build_opener(*handlers)
    try:
        with opener.open(request, timeout=1) as response:
            body = response.read(65537)
            if response.status != health.get("expected_status", 200):
                return HealthResult("occupied", f"HTTP {response.status}")
            if len(body) > 65536:
                return HealthResult("occupied", "resposta de saúde excede 64 KiB")
            if "expected_json" in health:
                try:
                    payload = json.loads(body)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return HealthResult("occupied", "resposta de saúde não é JSON válido")
                if not isinstance(payload, dict) or any(
                    payload.get(name) != value
                    for name, value in health["expected_json"].items()
                ):
                    return HealthResult("occupied", "identidade da resposta de saúde diverge")
            if "expected_text" in health:
                try:
                    actual = body.decode("utf-8").strip()
                except UnicodeDecodeError:
                    return HealthResult("occupied", "resposta de saúde não é UTF-8")
                if actual != health["expected_text"]:
                    return HealthResult("occupied", "conteúdo da resposta de saúde diverge")
            return HealthResult("healthy", f"HTTP {response.status}")
    except HTTPError as error:
        return HealthResult("occupied", f"HTTP {error.code}")
    except (OSError, URLError, TimeoutError) as error:
        # Não inicie outro processo sobre uma porta já ocupada. Uma sonda
        # inválida é degradação, não evidência suficiente de saúde.
        return HealthResult("occupied", str(error))


def start_project(
    project: dict[str, Any], *, wait_for_command: bool = False
) -> tuple[bool, str]:
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

    started_at = time.monotonic()
    deadline = started_at + orchestration["start"]["ready_timeout_seconds"]
    next_progress = 10
    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code not in (None, 0):
            pid_path.unlink(missing_ok=True)
            return False, f"inicialização terminou com código {return_code}; log {log_path}"
        if wait_for_command:
            if return_code == 0:
                pid_path.unlink(missing_ok=True)
                if health_result(project).state == "healthy":
                    return True, f"atualizado pelo SisTer; log {log_path}"
                return False, f"comando terminou, mas a saúde não foi confirmada; log {log_path}"
        elif health_result(project).state == "healthy":
            if return_code is not None:
                pid_path.unlink(missing_ok=True)
            return True, f"iniciado pelo SisTer; log {log_path}"
        elapsed = int(time.monotonic() - started_at)
        if elapsed >= next_progress:
            log(
                f"{project_id}: aguardando prontidão há {elapsed}s; "
                f"acompanhe {log_path}"
            )
            next_progress += 10
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
    healthy_count = 0
    for project in projects:
        project_id = project["id"]
        repository = repository_path(project)
        digest = source_digest(project, repository)
        health = health_result(project)
        if health.state == "healthy":
            if digest is not None and digest != recorded_digest(project_id):
                log(f"{project_id}: saudável, mas as fontes mudaram; atualizando")
                try:
                    success, detail = start_project(project, wait_for_command=True)
                except (OSError, RuntimeError, ValueError) as error:
                    success, detail = False, str(error)
                log(f"{project_id}: {'saudável' if success else 'falhou'} — {detail}")
                if success:
                    record_digest(project_id, digest)
                    healthy_count += 1
                else:
                    failures.append(
                        (project_id, project["orchestration"]["required"])
                    )
                continue
            healthy_count += 1
            log(f"{project_id}: saudável — já estava em execução")
            continue
        if health.state == "occupied":
            log(
                f"{project_id}: falhou — porta ocupada, mas a sonda de saúde "
                f"não confirmou o serviço ({health.detail})"
            )
            failures.append((project_id, project["orchestration"]["required"]))
            continue
        log(f"{project_id}: indisponível; iniciando pelo contrato local")
        try:
            success, detail = start_project(project)
        except (OSError, RuntimeError, ValueError) as error:
            success, detail = False, str(error)
        log(f"{project_id}: {'saudável' if success else 'falhou'} — {detail}")
        if not success:
            failures.append((project_id, project["orchestration"]["required"]))
        else:
            record_digest(project_id, digest)
            healthy_count += 1

    required_failures = [project_id for project_id, required in failures if required]
    if failures:
        log("degradação: " + ", ".join(project_id for project_id, _ in failures))
    else:
        log(f"{healthy_count} subsistema(s) governado(s) saudável(is)")
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
