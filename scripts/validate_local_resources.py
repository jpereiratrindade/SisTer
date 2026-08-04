#!/usr/bin/env python3
import json
import pathlib
import re
import sys
from urllib.parse import urlparse


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.lib.workspace_paths import repository_path as resolve_repository_path  # noqa: E402

REGISTRY = ROOT / "config" / "local_resources.json"


def fail(message: str) -> None:
    print(f"local resource validation error: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        fail("projects must be a non-empty list")

    project_ids: set[str] = set()
    endpoints: dict[tuple[str, int], str] = {}
    containers: dict[str, str] = {}
    volumes: dict[str, str] = {}

    for project in projects:
        project_id = project.get("id")
        if not isinstance(project_id, str) or not project_id:
            fail("every project must have an id")
        if project_id in project_ids:
            fail(f"duplicate project id: {project_id}")
        project_ids.add(project_id)

        if project.get("integrates_with_sister") and project_id not in {
            "sister", "sister_reference"
        }:
            fail(f"real subsystem must not be registered in SisTer core: {project_id}")

        repository = project.get("repository")
        integration_owner = project.get("integrates_with")
        if integration_owner is not None and (
            not isinstance(integration_owner, str) or not integration_owner
        ):
            fail(f"invalid integration owner in {project_id}")
        if (
            project.get("integrates_with_sister") or integration_owner
        ) and project_id != "sister":
            if repository is None:
                if project.get("status") != "planned":
                    fail(f"integrated project {project_id} has no repository")
            else:
                try:
                    repository_path = resolve_repository_path(ROOT, project)
                except RuntimeError:
                    repository_path = None
                link = repository_path / "SISTER_INTEGRATION.md" if repository_path else None
                if repository_path is not None and repository_path.is_dir() and not link.is_file():
                    fail(f"integrated project {project_id} lacks {link}")

        orchestration = project.get("orchestration")
        if orchestration is not None:
            if not (project.get("integrates_with_sister") or integration_owner):
                fail(f"orchestrated project {project_id} is not integrated")
            if repository is None:
                fail(f"orchestrated project {project_id} has no repository")
            policy = orchestration.get("policy")
            if policy != "ensure-running":
                fail(f"invalid orchestration policy in {project_id}")
            if policy == "ensure-running" and project_id != "sister_reference":
                fail(f"only sister_reference may be an operational validation target: {project_id}")
            if orchestration.get("environment") != "dev":
                fail(f"orchestration is only allowed for dev in {project_id}")
            if not isinstance(orchestration.get("required"), bool):
                fail(f"orchestration required flag must be boolean in {project_id}")

            health = orchestration.get("health")
            if not isinstance(health, dict):
                fail(f"orchestration health is missing in {project_id}")
            parsed_health = urlparse(health.get("url", ""))
            if (
                parsed_health.scheme not in {"http", "https"}
                or parsed_health.hostname not in {"127.0.0.1", "localhost"}
                or parsed_health.port is None
            ):
                fail(f"orchestration health must be a local HTTP URL in {project_id}")
            if parsed_health.scheme == "http" and health.get("tls_verify") is False:
                fail(f"tls_verify is invalid for HTTP in {project_id}")
            expected_status = health.get("expected_status", 200)
            if not isinstance(expected_status, int) or not 200 <= expected_status < 300:
                fail(f"orchestration health status is invalid in {project_id}")
            expected_json = health.get("expected_json")
            expected_text = health.get("expected_text")
            if (expected_json is None) == (expected_text is None):
                fail(
                    f"orchestration health must declare exactly one expected "
                    f"response in {project_id}"
                )
            if expected_json is not None and (
                not isinstance(expected_json, dict) or not expected_json
            ):
                fail(f"orchestration expected_json is invalid in {project_id}")
            if expected_text is not None and (
                not isinstance(expected_text, str) or not expected_text
            ):
                fail(f"orchestration expected_text is invalid in {project_id}")

            start = orchestration.get("start")
            argv = start.get("argv") if isinstance(start, dict) else None
            if not isinstance(argv, list) or not argv or not all(
                isinstance(item, str) and item for item in argv
            ):
                fail(f"orchestration argv is invalid in {project_id}")
            entrypoint = pathlib.PurePosixPath(argv[0])
            if not argv[0].startswith("./") or ".." in entrypoint.parts:
                fail(f"orchestration entrypoint is not governed in {project_id}")
            timeout = start.get("ready_timeout_seconds")
            if not isinstance(timeout, int) or not 5 <= timeout <= 600:
                fail(f"orchestration timeout is invalid in {project_id}")
            environment = start.get("environment", {})
            if not isinstance(environment, dict):
                fail(f"orchestration environment is invalid in {project_id}")
            for name, value in environment.items():
                if (
                    not re.fullmatch(r"[A-Z][A-Z0-9_]*", name)
                    or not isinstance(value, str)
                    or any(term in name for term in ("PASSWORD", "SECRET", "TOKEN", "KEY"))
                ):
                    fail(f"unsafe orchestration environment field in {project_id}")

            refresh = orchestration.get("refresh")
            if refresh is not None:
                if refresh.get("policy") != "on-source-change":
                    fail(f"orchestration refresh policy is invalid in {project_id}")
                refresh_paths = refresh.get("paths")
                if (
                    not isinstance(refresh_paths, list)
                    or not refresh_paths
                    or not all(isinstance(path, str) and path for path in refresh_paths)
                ):
                    fail(f"orchestration refresh paths are invalid in {project_id}")
                for path in refresh_paths:
                    source = pathlib.PurePosixPath(path)
                    if source.is_absolute() or ".." in source.parts:
                        fail(f"orchestration refresh path is unsafe in {project_id}")
                    try:
                        repository_path = resolve_repository_path(ROOT, project)
                    except RuntimeError:
                        repository_path = None
                    if (
                        repository_path is not None
                        and repository_path.is_dir()
                        and not (repository_path / path).exists()
                    ):
                        fail(
                            f"orchestration refresh path does not exist in {project_id}: "
                            f"{path}"
                        )

        for resource in project.get("resources", []):
            host = resource.get("host")
            port = resource.get("port")
            kind = resource.get("kind")
            if not isinstance(host, str) or not isinstance(port, int) or not kind:
                fail(f"invalid resource in {project_id}")
            if not 1 <= port <= 65535:
                fail(f"invalid port {port} in {project_id}")
            if orchestration is not None and host in {"0.0.0.0", "::"}:
                fail(f"governed subsystem cannot publish a wildcard endpoint: {project_id}:{port}")
            if orchestration is not None and kind in {"http", "https"}:
                if host not in {"127.0.0.1", "localhost", "::1"}:
                    fail(f"governed subsystem endpoint must be internal: {project_id}:{port}")
                if resource.get("exposure") != "internal":
                    fail(f"governed subsystem endpoint must declare internal exposure: {project_id}:{port}")

            bind_host = "*" if host in {"0.0.0.0", "::"} else host
            endpoint = (bind_host, port)
            wildcard = ("*", port)
            loopback = ("127.0.0.1", port)
            conflicts = {endpoint, wildcard}
            if bind_host == "*":
                conflicts.add(loopback)
            for candidate in conflicts:
                owner = endpoints.get(candidate)
                if owner is not None:
                    fail(f"port {port} conflicts between {owner} and {project_id}")
            endpoints[endpoint] = project_id

            for field, index in (("container", containers), ("volume", volumes)):
                value = resource.get(field)
                if value:
                    owner = index.get(value)
                    if owner is not None:
                        fail(f"{field} {value} is shared by {owner} and {project_id}")
                    index[value] = project_id

        if orchestration is not None:
            health_port = urlparse(orchestration["health"]["url"]).port
            declared_ports = {
                resource["port"]
                for resource in project.get("resources", [])
                if resource.get("environment") == orchestration["environment"]
                and resource.get("kind") in {"http", "https"}
            }
            if health_port not in declared_ports:
                fail(f"orchestration health port is not reserved by {project_id}")

    for project in projects:
        integration_owner = project.get("integrates_with")
        if integration_owner is not None and integration_owner not in project_ids:
            fail(f"{project['id']} integrates with unknown project {integration_owner}")
        for dependency in project.get("depends_on", []):
            owner = dependency.get("project")
            if owner not in project_ids:
                fail(f"{project['id']} depends on unknown project {owner}")

    print(
        f"local resource validation ok: {len(project_ids)} projects, "
        f"{len(endpoints)} endpoints"
    )


if __name__ == "__main__":
    main()
