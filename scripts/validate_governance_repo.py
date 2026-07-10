#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "docs/adr/README.md",
    "docs/architecture/DDD.md",
    "docs/dai/DAI.md",
    "policies/context_boundary_policy.md",
    "policies/evidence_and_audit_policy.md",
    "policies/approval_matrix.md",
    "mcp/contracts/modify_code.contract.json",
    "mcp/contracts/review_change.contract.json",
    "prompts/task_template.md",
    "prompts/governance_task_packet.md",
    "contracts/README.md",
]

missing = [path for path in REQUIRED if not (ROOT / path).exists()]
if missing:
    print("governance validation failed")
    for path in missing:
        print(f"- missing: {path}")
    sys.exit(1)

print("governance validation ok")
