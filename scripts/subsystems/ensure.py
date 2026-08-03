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
import re
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
sys.path.insert(0, str(ROOT))
from scripts.lib.workspace_paths import (  # noqa: E402
    integration_contracts,
    repository_path as resolve_repository_path,
)

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
    return resolve_repository_path(ROOT, project)


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
    port_hex = f"{endpoint.port:04X}"
    for table in (Path("/proc/net/tcp"), Path("/proc/net/tcp6")):
        try:
            rows = table.read_text(encoding="ascii").splitlines()[1:]
        except OSError:
            rows = []
        for row in rows:
            fields = row.split()
            if len(fields) < 4 or fields[3] != "0A":
                continue
            address, port = fields[1].split(":", 1)
            if port == port_hex and set(address) == {"0"}:
                return HealthResult("occupied", "listener wildcard viola a fronteira interna")
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
) -> tuple[bool, str, int | None]:
    project_id = project["id"]
    orchestration = project["orchestration"]
    repository = repository_path(project)
    argv = start_argv(project, repository)
    environment = os.environ.copy()
    environment["SISTER_HOME"] = str(ROOT)
    environment.update(orchestration["start"].get("environment", {}))

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    log_path = RUN_DIR / f"{project_id}.log"
    displayed_log = log_path.relative_to(ROOT)
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
            return False, f"inicialização terminou com código {return_code}; log {displayed_log}", None
        if wait_for_command:
            if return_code == 0:
                pid_path.unlink(missing_ok=True)
                if health_result(project).state == "healthy":
                    return True, f"atualizado pelo SisTer; log {displayed_log}", process.pid
                return False, f"comando terminou, mas a saúde não foi confirmada; log {displayed_log}", None
        elif health_result(project).state == "healthy":
            if return_code is not None:
                pid_path.unlink(missing_ok=True)
            return True, f"iniciado pelo SisTer; log {displayed_log}", process.pid
        elapsed = int(time.monotonic() - started_at)
        if elapsed >= next_progress:
            log(
                f"{project_id}: aguardando prontidão há {elapsed}s; "
                f"acompanhe {displayed_log}"
            )
            next_progress += 10
        time.sleep(1)

    if process.poll() is not None:
        pid_path.unlink(missing_ok=True)
    return False, f"não ficou saudável dentro do prazo; log {displayed_log}", None


def component_result(
    project_id: str,
    required: bool,
    status: str,
    phase: str,
    detail: str,
    started_at: float,
    started_by_run: bool,
    process_group: int | None = None,
) -> dict[str, Any]:
    exit_match = re.search(r"código (\d+)", detail)
    log_path = RUN_DIR / f"{project_id}.log"
    return {
        "component": project_id,
        "required": required,
        "status": status,
        "phase": phase,
        "exit_code": int(exit_match.group(1)) if exit_match else None,
        "elapsed_seconds": round(time.monotonic() - started_at, 3),
        "log": str(log_path.relative_to(ROOT)) if log_path.exists() else None,
        "started_by_run": started_by_run,
        "process_group": process_group,
        "detail": detail,
    }


def write_report(
    path: Path | None,
    environment: str,
    results: list[dict[str, Any]],
) -> str:
    failed = [result for result in results if result["status"] == "DEGRADED"]
    if any(result["required"] for result in failed):
        state = "BLOCKED"
    elif failed:
        state = "DEGRADED"
    else:
        state = "READY"
    if path is not None:
        payload = {
            "schema": "sister.subsystem-run/1.0.0",
            "environment": environment,
            "result": state,
            "components": results,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    return state


def ensure(
    environment: str,
    selected: set[str],
    required_by_profile: set[str],
    strict: bool,
    refresh_changed: bool,
    report_path: Path | None,
) -> int:
    projects = governed_projects(environment)
    if selected:
        projects = [project for project in projects if project["id"] in selected]
        missing = selected - {project["id"] for project in projects}
        if missing:
            raise RuntimeError(f"projetos não governados para {environment}: {', '.join(sorted(missing))}")
    if not projects:
        log(f"nenhum subsistema governado para o ambiente {environment}")
        write_report(report_path, environment, [])
        return 0

    results: list[dict[str, Any]] = []
    healthy_count = 0
    for project in projects:
        project_id = project["id"]
        required = bool(project["orchestration"]["required"] or strict or project_id in required_by_profile)
        started_at = time.monotonic()
        try:
            repository = repository_path(project)
            start_argv(project, repository)
            digest = source_digest(project, repository)
        except (OSError, RuntimeError, ValueError) as error:
            detail = str(error)
            log(f"{project_id}: falhou no preflight — {detail}")
            results.append(component_result(
                project_id, required, "DEGRADED", "preflight", detail, started_at, False
            ))
            continue
        health = health_result(project)
        if health.state == "healthy":
            if digest is not None and digest != recorded_digest(project_id):
                if refresh_changed:
                    log(f"{project_id}: saudável, mas as fontes mudaram; atualização explícita solicitada")
                    try:
                        success, detail, process_group = start_project(project, wait_for_command=True)
                    except (OSError, RuntimeError, ValueError) as error:
                        success, detail, process_group = False, str(error), None
                    log(f"{project_id}: {'saudável' if success else 'falhou'} — {detail}")
                    results.append(component_result(
                        project_id,
                        required,
                        "READY" if success else "DEGRADED",
                        "refresh",
                        detail,
                        started_at,
                        True,
                        process_group,
                    ))
                    if success:
                        record_digest(project_id, digest)
                        healthy_count += 1
                    continue
                log(f"{project_id}: saudável; fontes mudaram, atualização não solicitada")
            healthy_count += 1
            log(f"{project_id}: saudável — já estava em execução")
            results.append(component_result(
                project_id, required, "READY", "health", health.detail, started_at, False
            ))
            continue
        if health.state == "occupied":
            detail = f"porta ocupada sem saúde confirmada: {health.detail}"
            log(f"{project_id}: falhou — {detail}")
            results.append(component_result(
                project_id, required, "DEGRADED", "health", detail, started_at, False
            ))
            continue
        log(f"{project_id}: indisponível; iniciando pelo contrato local")
        try:
            success, detail, process_group = start_project(project)
        except (OSError, RuntimeError, ValueError) as error:
            success, detail, process_group = False, str(error), None
        log(f"{project_id}: {'saudável' if success else 'falhou'} — {detail}")
        results.append(component_result(
            project_id,
            required,
            "READY" if success else "DEGRADED",
            "startup",
            detail,
            started_at,
            True,
            process_group,
        ))
        if success:
            record_digest(project_id, digest)
            healthy_count += 1

    failures = [result for result in results if result["status"] == "DEGRADED"]
    required_failures = [result for result in failures if result["required"]]
    if failures:
        log("degradação: " + ", ".join(result["component"] for result in failures))
    else:
        log(f"{healthy_count} subsistema(s) governado(s) saudável(is)")
    write_report(report_path, environment, results)
    return 2 if required_failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", default="dev")
    parser.add_argument("--project", action="append", default=[])
    parser.add_argument("--require", action="append", default=[])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--refresh-changed", action="store_true")
    parser.add_argument("--report", type=Path)
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
    resolved: list[tuple[dict[str, Any], Path]] = []
    missing: list[str] = []
    for project in projects:
        try:
            repository = repository_path(project)
            start_argv(project, repository)
            resolved.append((project, repository))
        except (OSError, RuntimeError, ValueError) as error:
            if not args.check:
                raise
            missing.append(f"{project['id']}: {error}")
    if args.check:
        registered = {project["id"] for project, _repository in resolved}
        governed_contracts = sorted(
            project["id"]
            for project, repository in resolved
            if (repository / "SISTER_INTEGRATION.md").is_file()
        )
        discovered = integration_contracts(ROOT)
        unmanaged = sorted(project_id for project_id in discovered if project_id not in registered)
        if governed_contracts:
            log("contratos governados encontrados: " + ", ".join(governed_contracts))
        if unmanaged:
            log("contratos fora da seleção governada: " + ", ".join(unmanaged))
        if missing:
            log("informe a localização dos subsistemas ausentes:")
            for detail in missing:
                log(f"  - {detail}")
            return 3
    elif missing:
        raise RuntimeError("; ".join(missing))
    if args.check:
        log(
            f"configuração válida para {len(projects)} subsistema(s): "
            + ", ".join(project["id"] for project in projects)
        )
        return 0

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    with (RUN_DIR / "ensure.lock").open("w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return ensure(
            args.environment,
            selected,
            set(args.require),
            args.strict,
            args.refresh_changed,
            args.report,
        )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, TypeError, ValueError, RuntimeError) as error:
        print(f"[subsistemas] erro de configuração: {error}", file=sys.stderr)
        raise SystemExit(3)
