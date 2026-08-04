#!/usr/bin/env python3
"""Small local persistence boundary for proposed participation contracts."""
import json
import os
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/participation/1.0.0/participation-contract.schema.json"


def store_path() -> Path:
    configured = os.environ.get("SISTER_PARTICIPATION_STORE")
    if not configured:
        raise ValueError("SISTER_PARTICIPATION_STORE must be explicitly configured")
    path = Path(configured)
    if not path.is_absolute():
        raise ValueError("SISTER_PARTICIPATION_STORE must be an absolute path")
    return path


def fail(message: str) -> int:
    print(f"participation error: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) not in {3, 4} or sys.argv[1] not in {"register", "show"}:
        print("usage: participation_store.py register <contract.json> | show <participation_id>", file=sys.stderr)
        return 2
    try:
        root = store_path()
        root.mkdir(mode=0o750, parents=True, exist_ok=True)
        if sys.argv[1] == "show":
            identifier = sys.argv[2]
            path = root / f"{identifier}.json"
            if not path.is_file():
                return fail(f"participation not found: {identifier}")
            print(path.read_text(encoding="utf-8"))
            return 0
        if len(sys.argv) != 3:
            return 2
        source = Path(sys.argv[2])
        contract = json.loads(source.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        schemas = {schema["$id"]: schema}
        for dependency in SCHEMA.parent.glob("*.schema.json"):
            value = json.loads(dependency.read_text(encoding="utf-8"))
            schemas[value["$id"]] = value
        resolver = jsonschema.RefResolver.from_schema(schema, store=schemas)
        jsonschema.Draft202012Validator(schema, resolver=resolver).validate(contract)
        identifier = contract["participation_id"]
        destination = root / f"{identifier}.json"
        if destination.exists():
            return fail(f"participation already registered: {identifier}")
        temporary = root / f".{identifier}.json.tmp"
        temporary.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o640)
        temporary.replace(destination)
        print(f"participation registered: {identifier}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, jsonschema.ValidationError) as exc:
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
