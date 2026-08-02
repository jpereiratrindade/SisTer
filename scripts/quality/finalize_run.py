#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
QUALITY_REPORT = ROOT / ".run" / "maturity" / "quality.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--subsystems-report", type=Path)
    args = parser.parse_args()

    quality = json.loads(QUALITY_REPORT.read_text(encoding="utf-8"))
    if quality.get("result") != "PASS":
        raise ValueError("core quality report is not PASS")

    subsystem_state = "NOT_REQUESTED"
    components = []
    if args.subsystems_report:
        subsystem_report = json.loads(args.subsystems_report.read_text(encoding="utf-8"))
        subsystem_state = subsystem_report["result"]
        components = subsystem_report["components"]

    if subsystem_state == "BLOCKED":
        overall = "BLOCKED"
    elif subsystem_state == "DEGRADED":
        overall = "PASS_WITH_DEGRADATION"
    else:
        overall = "PASS"

    quality["result"] = overall
    quality["execution"] = {
        "profile": args.profile,
        "core_quality": "PASS",
        "sisterd_readiness": "READY",
        "core_smoke": "PASS",
        "subsystems": subsystem_state,
        "components": components,
        "overall": overall,
        "gate_closure_authorized": False,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    temporary = QUALITY_REPORT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(quality, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(QUALITY_REPORT)

    print("\nSisTer execution summary")
    print(f"  Profile:              {args.profile}")
    print("  Core quality:         PASS")
    print("  sisterd readiness:    READY")
    print("  Core smoke:           PASS")
    print(f"  Subsystems:           {subsystem_state}")
    for component in components:
        print(f"    {component['component']}: {component['status']} ({component['phase']})")
    print(f"  Overall:              {overall}")
    print("  Gate closure:         NOT_AUTHORIZED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"run summary error: {error}", file=sys.stderr)
        sys.exit(3)
