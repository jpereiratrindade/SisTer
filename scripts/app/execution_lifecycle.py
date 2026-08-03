#!/usr/bin/env python3
"""Track and stop resources owned by one run_all execution."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time


ROOT = Path(__file__).resolve().parents[2]
EXECUTIONS = ROOT / ".run" / "executions"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def running_containers() -> set[str]:
    for command in (["podman", "ps", "--format", "{{.Names}}"], ["docker", "ps", "--format", "{{.Names}}"]):
        try:
            result = subprocess.run(command, text=True, capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0:
            return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return set()


def candidate_containers(payload: dict, component_ids: set[str] | None = None) -> set[str]:
    registry = json.loads((ROOT / "config" / "local_resources.json").read_text(encoding="utf-8"))
    allowed = {"sister"}
    if component_ids is not None:
        allowed |= component_ids
    elif payload.get("profile") not in {"dev-core", "test-core"}:
        allowed |= {
            project["id"] for project in registry["projects"]
            if project.get("orchestration", {}).get("environment") == payload["environment"]
            and project.get("orchestration", {}).get("policy") == "ensure-running"
        }
    return {
        resource["container"]
        for project in registry["projects"] if project["id"] in allowed
        for resource in project.get("resources", [])
        if resource.get("environment") == payload["environment"] and resource.get("container")
    }


def state_path(environment: str) -> Path:
    return EXECUTIONS / f"active-{environment}.json"


def write_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def begin(args: argparse.Namespace) -> int:
    path = state_path(args.environment)
    if path.exists():
        raise RuntimeError(f"active execution already exists for {args.environment}; stop it first")
    payload = {
        "schema": "sister.execution-state/1.0.0",
        "execution_id": f"{int(time.time())}-{os.getpid()}",
        "profile": args.profile,
        "environment": args.environment,
        "access_scope": args.access_scope,
        "status": "STARTING",
        "started_at": now(),
        "containers_before": sorted(running_containers()),
        "owned_process_groups": [],
        "owned_containers": [],
        "reused_containers": [],
    }
    write_state(path, payload)
    print(path.relative_to(ROOT))
    return 0


def numeric_pid(path: Path) -> int | None:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if raw.isdigit():
        return int(raw)
    try:
        value = json.loads(raw).get("pid")
        return value if isinstance(value, int) else None
    except (json.JSONDecodeError, AttributeError):
        return None


def finalize(args: argparse.Namespace) -> int:
    path = state_path(args.environment)
    payload = json.loads(path.read_text(encoding="utf-8"))
    before = set(payload["containers_before"])
    after = running_containers()
    groups: list[dict] = []
    if args.subsystems_report and args.subsystems_report.exists():
        report = json.loads(args.subsystems_report.read_text(encoding="utf-8"))
        for component in report.get("components", []):
            pgid = component.get("process_group")
            if component.get("started_by_run") and isinstance(pgid, int):
                groups.append({"component": component["component"], "pgid": pgid})
        component_ids = {component["component"] for component in report.get("components", [])}
    else:
        component_ids = set()
    candidates = candidate_containers(payload, component_ids)
    payload["container_candidates"] = sorted(candidates)
    payload["owned_containers"] = sorted((after - before) & candidates)
    payload["reused_containers"] = sorted(after & before & candidates)
    payload["owned_process_groups"] = groups
    payload["owned_processes"] = {
        "sisterd": numeric_pid(ROOT / ".run" / f"sisterd-{args.environment}.pid"),
        "gateway": numeric_pid(ROOT / ".run" / "gateway" / "haproxy.pid"),
        "gateway_sisterd": numeric_pid(ROOT / ".run" / "gateway" / "lan-sisterd.pid"),
    }
    payload["status"] = "RUNNING"
    payload["ready_at"] = now()
    write_state(path, payload)
    return 0


def group_members(pgid: int) -> list[int]:
    members = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if os.getpgid(int(entry.name)) == pgid:
                members.append(int(entry.name))
        except (OSError, ProcessLookupError):
            continue
    return members


def belongs_to_sister(pid: int) -> bool:
    try:
        environment = (Path("/proc") / str(pid) / "environ").read_bytes().split(b"\0")
    except OSError:
        return False
    marker = f"SISTER_HOME={ROOT}".encode()
    return marker in environment


def stop_group(pgid: int) -> bool:
    members = group_members(pgid)
    if not members:
        return False
    if not all(belongs_to_sister(pid) for pid in members):
        raise RuntimeError(f"refusing unowned process group {pgid}")
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return False
    for _ in range(50):
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    return False


def stop_container(name: str) -> bool:
    for runtime in ("podman", "docker"):
        try:
            result = subprocess.run([runtime, "stop", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0:
            return True
    return False


def stop(args: argparse.Namespace) -> int:
    path = state_path(args.environment)
    if not path.exists():
        subprocess.run([str(ROOT / "scripts/app/stop.sh"), args.environment, "--core-only"])
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    stopped_groups = []
    for item in reversed(payload.get("owned_process_groups", [])):
        if stop_group(item["pgid"]):
            stopped_groups.append(item["component"])
    owned_processes = payload.get("owned_processes", {})
    if owned_processes.get("gateway") or owned_processes.get("gateway_sisterd"):
        environment = os.environ.copy()
        environment["SISTER_COMPONENT_STOP_ONLY"] = "1"
        subprocess.run(
            [str(ROOT / "scripts/stop_gateway_lan_lab.sh")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=environment,
        )
        subprocess.run([str(ROOT / "scripts/stop_gateway_lab.sh")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([str(ROOT / "scripts/app/stop.sh"), args.environment, "--core-only"])
    current = running_containers()
    owned = set(payload.get("owned_containers", []))
    if payload.get("status") == "STARTING":
        owned |= (
            current - set(payload.get("containers_before", []))
        ) & candidate_containers(payload)
    stopped_containers = [name for name in sorted(owned) if name in current and stop_container(name)]
    payload["status"] = "STOPPED"
    payload["stopped_at"] = now()
    payload["stopped_process_groups"] = stopped_groups
    payload["stopped_containers"] = stopped_containers
    history = EXECUTIONS / f"{payload['execution_id']}.json"
    write_state(history, payload)
    path.unlink()
    print("SisTer execution stopped")
    print("  Owned process groups: " + (", ".join(stopped_groups) or "none"))
    print("  Owned containers:     " + (", ".join(stopped_containers) or "none"))
    print("  Reused resources:     preserved")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    begin_parser = subparsers.add_parser("begin")
    begin_parser.add_argument("--profile", required=True)
    begin_parser.add_argument("--environment", required=True)
    begin_parser.add_argument("--access-scope", required=True)
    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--environment", required=True)
    finalize_parser.add_argument("--subsystems-report", type=Path)
    stop_parser = subparsers.add_parser("stop")
    stop_parser.add_argument("--environment", required=True)
    args = parser.parse_args()
    return {"begin": begin, "finalize": finalize, "stop": stop}[args.command](args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"execution lifecycle error: {error}", file=os.sys.stderr)
        raise SystemExit(3)
