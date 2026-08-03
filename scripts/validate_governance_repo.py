#!/usr/bin/env python3
import json
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
    "contracts/integration_agreement.schema.json",
    "contracts/integration_receipt.schema.json",
    "contracts/subsystem/1.0.0/interface.json",
    "contracts/subsystem/1.0.0/identity.schema.json",
    "contracts/subsystem/1.0.0/echo.schema.json",
    "contracts/participation/1.0.0/participation-contract.schema.json",
    "contracts/participation/1.0.0/boundary-object-envelope.schema.json",
    "contracts/participation/1.0.0/participation-assessment.schema.json",
    "docs/work-packages/WP-MVP01-01-participation-model.md",
    "docs/adr/ADR-0008-bilateral-integration-agreements.md",
    "reference/sister-reference/manifest.json",
    "docs/governance/ARTIFACT_STATUS.md",
    "docs/governance/SUBSYSTEM_CONFORMANCE.md",
    "docs/adr/ADR-0023-mvp01-governed-participation.md",
    "docs/work-packages/WP-MVP01-00A-baseline.md",
    "engineering/baselines/mvp-00.json",
    "docs/adr/ADR-0020-specialized-http-gateway.md",
    "docs/security/GATEWAY_SECURITY_PROFILE.md",
    "docs/operations/GATEWAY_LAN_LAB.md",
    "contracts/gateway_security_profile.schema.json",
    "ops/gateway/security-profile.json",
    "scripts/validate_gateway_security_profile.py",
    "tests/gateway_security_profile_test.py",
    "ops/gateway/haproxy/haproxy.cfg.in",
    "ops/gateway/haproxy/README.md",
    "scripts/render_gateway_config.py",
    "scripts/validate_gateway_config.sh",
    "tests/gateway_config_render_test.py",
    "scripts/create_gateway_lab_certificate.sh",
    "scripts/run_gateway_lab.sh",
    "scripts/stop_gateway_lab.sh",
    "scripts/run_gateway_lan_lab.sh",
    "scripts/stop_gateway_lan_lab.sh",
    "scripts/check_gateway_lan_access.sh",
    "scripts/bootstrap_gateway_lan_admin.sh",
    "scripts/prod01_readiness.py",
    "tests/prod01_readiness_test.py",
    "docs/operations/PROD-01.md",
    "scripts/app/socket_activation_lab.py",
    "tests/gateway_protocol_test.py",
    "tests/gateway_header_sanitization_test.py",
    "tests/gateway_failure_test.py",
    "tests/gateway_lab_test.py",
    "tests/gateway_lab_support.py",
    "docs/evidence/security/SEC-03B.md",
    "ops/gateway/haproxy/errors/400.http",
    "ops/gateway/haproxy/errors/403.http",
    "ops/gateway/haproxy/errors/405.http",
    "ops/gateway/haproxy/errors/408.http",
    "ops/gateway/haproxy/errors/413.http",
    "ops/gateway/haproxy/errors/503.http",
]

missing = [path for path in REQUIRED if not (ROOT / path).exists()]
if missing:
    print("governance validation failed")
    for path in missing:
        print(f"- missing: {path}")
    sys.exit(1)

def load_json(path):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"governance validation failed\n- invalid JSON: {path}: {exc}")
        sys.exit(1)


reference_manifest = load_json("reference/sister-reference/manifest.json")
subsystem_interface = load_json("contracts/subsystem/1.0.0/interface.json")

policy_errors = []
if reference_manifest.get("system_id") != "sister_reference":
    policy_errors.append("reference subsystem id is invalid")
if reference_manifest.get("contract") != "sister.subsystem/1.0.0":
    policy_errors.append("reference subsystem contract is invalid")
if reference_manifest.get("production_eligible") is not False:
    policy_errors.append("reference subsystem must not be production eligible")
if subsystem_interface.get("contract") != reference_manifest.get("contract"):
    policy_errors.append("reference subsystem interface and manifest diverge")
interface_endpoints = {
    endpoint.get("name"): endpoint.get("path")
    for endpoint in subsystem_interface.get("endpoints", [])
    if isinstance(endpoint, dict)
}
if reference_manifest.get("technical_endpoints") != interface_endpoints:
    policy_errors.append("reference subsystem canonical endpoints diverge")
if policy_errors:
    print("governance validation failed")
    for error in policy_errors:
        print(f"- {error}")
    sys.exit(1)

print("governance validation ok")
