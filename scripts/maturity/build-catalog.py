#!/usr/bin/env python3
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def read_yaml(path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main():
    profiles_dir = ROOT / "engineering/maturity/profiles"
    catalog = {
        "schema": "sister.maturity-catalog/1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "components": [],
    }
    for profile_path in sorted(profiles_dir.glob("*.yaml")):
        profile = read_yaml(profile_path) or {}
        component_id = profile.get("id", profile_path.stem)
        checks = []
        by_stage = defaultdict(int)
        for suite in profile.get("check_suites", []):
            suite_path = ROOT / suite
            if not suite_path.exists():
                continue
            for check in read_yaml(suite_path) or []:
                stage = check.get("stage", "unknown")
                by_stage[stage] += 1
                checks.append({
                    "id": check.get("id", ""),
                    "stage": stage,
                    "type": check.get("type", ""),
                    "mandatory": bool(check.get("mandatory", False)),
                    "description": check.get("description", ""),
                    "suite": suite,
                })
        catalog["components"].append({
            "component_id": component_id,
            "label": profile.get("name", component_id),
            "evaluation_mode": profile.get("evaluation_mode", "governed"),
            "total_checks": len(checks),
            "checks_by_stage": dict(sorted(by_stage.items())),
            "checks": checks,
        })

    out = ROOT / ".run/maturity/catalog.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out)
    print(f"maturity catalog updated: {out}")


if __name__ == "__main__":
    main()
