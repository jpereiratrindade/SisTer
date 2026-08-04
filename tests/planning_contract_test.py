#!/usr/bin/env python3
import subprocess
import sys
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, str(ROOT / "scripts/planning/validate.py")], cwd=ROOT, check=True)
    commands = [
        ["plan", "status"],
        ["plan", "list", "--json"],
        ["plan", "gaps", "--json"],
        ["plan", "explain", "PDE-MVP01-01"],
    ]
    for command in commands:
        subprocess.run([sys.executable, str(ROOT / "scripts/sge"), *command], cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory() as directory:
        plan_copy = Path(directory) / "plan.json"
        plan_copy.write_text((ROOT / "engineering/planning/plan.json").read_text(encoding="utf-8"), encoding="utf-8")
        decision_path = Path(directory) / "decision.json"
        decision_path.write_text(json.dumps({
            "schema": "sister.planning-decision/1.0.0",
            "decision_id": "PLAN-DECISION-MVP01-01",
            "action_id": "PDE-MVP01-01",
            "decision": "approve",
            "authorized_transition": "IDEA->PRIORITIZED",
            "actor": "coordination.mvp01",
            "authority": "mvp01.plan.decide",
            "reason": "A persistência é a próxima lacuna crítica do MVP-01.",
            "assessment_id": "PLAN-ASSESS-MVP01-01",
            "origin_baseline": "db0edb5",
            "decision_commit": "431e6d5f6d20a863ae478a8f1e0a394fd1535d47c",
            "valid_until": "2026-12-31T23:59:59Z",
            "plan_revision": "PLAN-REV-INITIAL",
            "decided_at": "2026-08-03T00:00:00Z"
        }), encoding="utf-8")
        env = {**os.environ, "SISTER_PLAN_PATH": str(plan_copy)}
        subprocess.run([sys.executable, str(ROOT / "scripts/sge"), "plan", "assess", "PDE-MVP01-01", "--persist"], cwd=ROOT, env=env, check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/sge"), "plan", "decision", "record", str(decision_path)], cwd=ROOT, env=env, check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/sge"), "plan", "transition", "PDE-MVP01-01", "PRIORITIZED", "--decision-id", "PLAN-DECISION-MVP01-01"], cwd=ROOT, env=env, check=True)
        result = subprocess.run([sys.executable, str(ROOT / "scripts/sge"), "plan", "transition", "PDE-MVP01-01", "IN_PROGRESS", "--decision-id", "PLAN-DECISION-MVP01-01"], cwd=ROOT, env=env)
        assert result.returncode == 1, "a decision must not authorize a second transition"
        state = json.loads(plan_copy.read_text(encoding="utf-8"))
        assert state["actions"][0]["state"] == "PRIORITIZED"
        assert state["revisions"][-1]["revision_id"] == "PLAN-REV-MVP01-01-PRIORITIZED"
    print("planning CLI validation ok")


if __name__ == "__main__":
    main()
