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
    "contracts/sister_studio_capabilities.schema.json",
    "contracts/sister_studio_health.schema.json",
    "contracts/sister_clima_governance.schema.json",
    "contracts/camposync_package.schema.json",
    "docs/adr/ADR-0004-sister-studio-service-integration.md",
    "docs/governance/SISTER_STUDIO_DATA.md",
    "adapters/sister_studio/README.md",
    "examples/sister_studio_manifest_example.json",
    "adapters/sister_clima/README.md",
    "examples/sister_clima_manifest_example.json",
    "examples/sister_clima_governance_example.json",
    "docs/adr/ADR-0005-sister-clima-noncommercial-governance.md",
    "docs/governance/SISTER_CLIMA_DATA.md",
    "docs/adr/ADR-0006-sister-campo-federated-integration.md",
    "docs/adr/ADR-0007-nexo-research-operations-and-procurement.md",
    "adapters/sister_campo/README.md",
    "examples/sister_campo_manifest_example.json",
    "docs/governance/SISTER_NEXO.md",
    "docs/governance/NEXO_COMPRAS.md",
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


climate_policy = load_json("examples/sister_clima_governance_example.json")
climate_manifest = load_json("examples/sister_clima_manifest_example.json")
load_json("contracts/sister_clima_governance.schema.json")

policy_errors = []
if climate_policy.get("contract_id") != "sister-clima.governance":
    policy_errors.append("Sister-Clima governance contract id is invalid")
if climate_policy.get("contract_version") != "1.0.0":
    policy_errors.append("Sister-Clima governance contract version is invalid")
if climate_manifest.get("governance_contract") != "sister-clima.governance/1.0.0":
    policy_errors.append("Sister-Clima manifest does not reference governance/1.0.0")
if climate_policy.get("access", {}).get("entry_authentication") != "required":
    policy_errors.append("Sister-Clima entry authentication must be required")
if climate_policy.get("access", {}).get("direct_url_publication") != "prohibited":
    policy_errors.append("Sister-Clima direct URL publication must be prohibited")
if climate_policy.get("commercial_use", {}).get("allowed") is not False:
    policy_errors.append("Sister-Clima commercial use must be denied")
source_ids = {
    source.get("source_id")
    for source in climate_policy.get("data_sources", [])
    if isinstance(source, dict)
}
if not {"open_meteo", "nasa_power"}.issubset(source_ids):
    policy_errors.append("Sister-Clima governed sources must include Open-Meteo and NASA POWER")
required_metadata = set(
    climate_policy.get("output_policy", {}).get("required_metadata", [])
)
if not {
    "source",
    "data_license",
    "attribution",
    "modification_notice",
    "responsible_operator",
    "schema_version",
}.issubset(required_metadata):
    policy_errors.append("Sister-Clima output metadata is incomplete")

if policy_errors:
    print("governance validation failed")
    for error in policy_errors:
        print(f"- {error}")
    sys.exit(1)

print("governance validation ok")
