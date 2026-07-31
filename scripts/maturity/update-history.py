#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path

from status_contract import HISTORY_SCHEMA, atomic_write_json, load_json, validate_history, validate_status


def main():
    parser = argparse.ArgumentParser(description="Archive a SisTer maturity status")
    parser.add_argument("latest")
    parser.add_argument("history_root")
    arguments = parser.parse_args()

    latest = load_json(arguments.latest)
    errors = validate_status(latest)
    if errors:
        raise SystemExit("cannot archive invalid status: " + "; ".join(errors))

    history_root = Path(arguments.history_root)
    history_root.mkdir(parents=True, exist_ok=True)
    timestamp = latest["generated_at"].replace("-", "").replace(":", "").replace("Z", "Z")
    filename = f"{timestamp}-{latest['target_stage']}-{latest['source']['short_commit']}.json"
    destination = history_root / filename
    temporary = history_root / f".{filename}.tmp"
    shutil.copyfile(arguments.latest, temporary)
    temporary.replace(destination)

    index_path = history_root / "index.json"
    items = []
    if index_path.is_file():
        try:
            existing = load_json(index_path)
            if not validate_history(existing):
                items = existing["items"]
        except (OSError, ValueError):
            items = []
    relative_path = f"history/{filename}"
    current = {
        "generated_at": latest["generated_at"],
        "target_stage": latest["target_stage"],
        "result": latest["result"],
        "short_commit": latest["source"]["short_commit"],
        "passed": latest["summary"]["passed"],
        "failed": latest["summary"]["failed"],
        "warned": latest["summary"]["warned"],
        "relative_path": relative_path,
    }
    items = [current] + [item for item in items if item["relative_path"] != relative_path]
    payload = {"schema": HISTORY_SCHEMA, "items": items[:100]}
    errors = validate_history(payload)
    if errors:
        raise SystemExit("cannot publish invalid history: " + "; ".join(errors))
    atomic_write_json(index_path, payload)


if __name__ == "__main__":
    main()
