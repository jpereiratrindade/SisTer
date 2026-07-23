#!/usr/bin/env python3
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "local_resources.json"
DEV_ROOT = ROOT.parents[1]


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

        repository = project.get("repository")
        if project.get("integrates_with_sister") and project_id != "sister":
            if repository is None:
                if project.get("status") != "planned":
                    fail(f"integrated project {project_id} has no repository")
            else:
                repository_path = DEV_ROOT / repository
                link = repository_path / "SISTER_INTEGRATION.md"
                if repository_path.is_dir() and not link.is_file():
                    fail(f"integrated project {project_id} lacks {link}")

        for resource in project.get("resources", []):
            host = resource.get("host")
            port = resource.get("port")
            kind = resource.get("kind")
            if not isinstance(host, str) or not isinstance(port, int) or not kind:
                fail(f"invalid resource in {project_id}")
            if not 1 <= port <= 65535:
                fail(f"invalid port {port} in {project_id}")

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

    for project in projects:
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
