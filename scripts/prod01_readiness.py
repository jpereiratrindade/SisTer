#!/usr/bin/env python3
"""Aggregate the technical and operational evidence for PROD-01."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / ".run/production/prod01-readiness.json"
DEFAULT_PROMOTION_REPORT = ROOT / ".run/production/PROD-01-promotion-report.md"
DEFAULT_CORE_STATE = ROOT / ".run/production/core-state.json"
QUALITY_REPORT = ROOT / ".run/maturity/quality.json"
ENV_EVIDENCE = ROOT / "docs/evidence/security/SEC-03V-ENV.md"
GATE_EVIDENCE = ROOT / "docs/evidence/security/SEC-03V.md"
SECURITY_PROFILE = ROOT / "ops/gateway/security-profile.json"
AUTHORIZATION_EVIDENCE = ROOT / "docs/evidence/operations/PROD-01-G6-authorization.md"
MVP_VERSION = "v0.1.0"
PROMOTION_TAG = "prod-mvp-v0.1.0"
PRODUCT_MATURITY = "Beta"
AUTHORIZED_CORE_STATE = "Produção MVP"
PENDING_CORE_STATE = "Promotion pending"
TECHNICAL_GATE_IDS = {"G1", "G2", "G3", "G4", "G5"}


@dataclass(frozen=True)
class Gate:
    gate: str
    objective: str
    status: str
    detail: str
    evidence: list[str]


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def evidence_marker(path: Path, pattern: str) -> bool:
    try:
        return re.search(pattern, read(path), re.IGNORECASE | re.MULTILINE) is not None
    except OSError:
        return False


def quality_gate() -> Gate:
    evidence = [str(QUALITY_REPORT.relative_to(ROOT))]
    try:
        payload = json.loads(read(QUALITY_REPORT))
    except (OSError, json.JSONDecodeError):
        return Gate("G1", "Plataforma", "BLOCKED", "relatório de qualidade ausente ou inválido", evidence)
    current = git("rev-parse", "HEAD")
    report_commit = payload.get("source", {}).get("commit")
    worktree = payload.get("source", {}).get("worktree")
    skipped = payload.get("summary", {}).get("skipped", 0)
    if payload.get("result") != "PASS":
        return Gate("G1", "Plataforma", "BLOCKED", "run_quality não terminou em PASS", evidence)
    if report_commit != current:
        return Gate("G1", "Plataforma", "BLOCKED", "relatório de qualidade pertence a outro commit", evidence)
    if worktree != "clean" or git("status", "--porcelain"):
        return Gate("G1", "Plataforma", "BLOCKED", "worktree atual ou relatório de qualidade não está limpo", evidence)
    if skipped:
        return Gate("G1", "Plataforma", "BLOCKED", f"relatório contém {skipped} teste(s) SKIP", evidence)
    return Gate("G1", "Plataforma", "PASS", "qualidade PASS no commit atual sem skips", evidence)


def security_gate() -> Gate:
    evidence = [str(ENV_EVIDENCE.relative_to(ROOT)), str(GATE_EVIDENCE.relative_to(ROOT))]
    try:
        json.loads(read(SECURITY_PROFILE))
    except (OSError, json.JSONDecodeError):
        return Gate("G2", "Segurança", "BLOCKED", "perfil de segurança ausente ou inválido", evidence)
    env_ready = evidence_marker(ENV_EVIDENCE, r"\*\*Estado:\*\*\s*`READY`") and evidence_marker(
        ENV_EVIDENCE, r"(?:42/42 PASS|checks\s+42\s+PASS\s+42)"
    )
    gate_pass = evidence_marker(GATE_EVIDENCE, r"\*\*Estado:\*\*\s*`PASS`") and evidence_marker(
        GATE_EVIDENCE, r"7/7 PASS\s+0 SKIP\s+0 FAIL"
    )
    if not env_ready or not gate_pass:
        return Gate("G2", "Segurança", "BLOCKED", "evidência SEC-03V não está READY/PASS completa", evidence)
    return Gate("G2", "Segurança", "PASS", "SEC-03V-ENV READY e SEC-03V PASS sem skips", evidence)


def operational_evidence(gate_id: str, objective: str, filename: str, requirements: str) -> Gate:
    path = ROOT / "docs/evidence/operations" / filename
    relative = str(path.relative_to(ROOT))
    if not path.is_file():
        return Gate(gate_id, objective, "PENDING", f"evidência pendente: {requirements}", [relative])
    if not evidence_marker(path, r"(?m)^(?:status|estado):\s*PASS\s*$"):
        return Gate(gate_id, objective, "BLOCKED", "evidência existe, mas não declara status PASS", [relative])
    return Gate(gate_id, objective, "PASS", "evidência operacional aprovada", [relative])


def authorization_gate(commit: str) -> Gate:
    evidence = [display_path(AUTHORIZATION_EVIDENCE)]
    if not AUTHORIZATION_EVIDENCE.is_file():
        return Gate(
            "G6",
            "Promoção",
            "AWAITING_AUTHORIZATION",
            "revisão formal de governança ainda necessária",
            evidence + ["docs/evidence/approval-template.md"],
        )
    authorized = evidence_marker(AUTHORIZATION_EVIDENCE, r"(?m)^(?:status|estado|decision|decisão):\s*AUTHORIZED\s*$")
    release = evidence_marker(AUTHORIZATION_EVIDENCE, rf"(?m)^release:\s*{re.escape(MVP_VERSION)}\s*$")
    git_tag = evidence_marker(AUTHORIZATION_EVIDENCE, rf"(?m)^git_tag:\s*{re.escape(PROMOTION_TAG)}\s*$")
    owner = evidence_marker(AUTHORIZATION_EVIDENCE, r"(?m)^(?:authorized_by|approved_by):\s*\S.+$")
    timestamp = evidence_marker(AUTHORIZATION_EVIDENCE, r"(?m)^(?:authorized_at|approved_at):\s*\S.+$")
    rollback = evidence_marker(AUTHORIZATION_EVIDENCE, r"(?m)^rollback_reference:\s*\S.+$")
    limitations = evidence_marker(AUTHORIZATION_EVIDENCE, r"(?m)^known_limitations:\s*\S.+$")
    if not authorized:
        return Gate("G6", "Promoção", "BLOCKED", "autorização existe, mas não declara AUTHORIZED", evidence)
    if not evidence_marker(AUTHORIZATION_EVIDENCE, rf"(?m)^commit:\s*{re.escape(commit)}\s*$"):
        return Gate("G6", "Promoção", "BLOCKED", "autorização pertence a outro commit", evidence)
    missing = []
    if not release:
        missing.append("release")
    if not git_tag:
        missing.append("git_tag")
    if not owner:
        missing.append("authorized_by")
    if not timestamp:
        missing.append("authorized_at")
    if not rollback:
        missing.append("rollback_reference")
    if not limitations:
        missing.append("known_limitations")
    if missing:
        return Gate("G6", "Promoção", "BLOCKED", "autorização incompleta: " + ", ".join(missing), evidence)
    return Gate("G6", "Promoção", "AUTHORIZED", "promoção operacional autorizada para o commit avaliado", evidence)


def build_gates(commit: str) -> list[Gate]:
    return [
        quality_gate(),
        security_gate(),
        operational_evidence("G3", "Operação", "PROD-01-G3-operations.md", "reinício, reboot, atualização, certificado e logs"),
        operational_evidence("G4", "Recuperação", "PROD-01-G4-recovery.md", "backup/restauração, rollback e reinício de serviços"),
        operational_evidence("G5", "Observabilidade", "PROD-01-G5-observability.md", "health, métricas, logs, auditoria e carga"),
        authorization_gate(commit),
    ]


def technical_status(gates: list[Gate]) -> str:
    technical_gates = [gate for gate in gates if gate.gate in TECHNICAL_GATE_IDS]
    present = {gate.gate for gate in technical_gates}
    if present != TECHNICAL_GATE_IDS:
        return "NOT_READY"
    if any(gate.status == "BLOCKED" for gate in technical_gates):
        return "BLOCKED"
    if all(gate.status == "PASS" for gate in technical_gates):
        return "READY"
    return "NOT_READY"


def promotion_decision(gates: list[Gate], technical: str) -> tuple[str, bool]:
    g6 = next((gate for gate in gates if gate.gate == "G6"), None)
    if technical == "READY" and g6 and g6.status == "AUTHORIZED":
        return "AUTHORIZED", True
    if g6 and g6.status == "BLOCKED":
        return "BLOCKED", False
    return "AWAITING_AUTHORIZATION", False


def write_report(path: Path, gates: list[Gate], commit: str) -> dict:
    technical = technical_status(gates)
    decision, production_authorized = promotion_decision(gates, technical)
    payload = {
        "schema": "sister.prod01-readiness/1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "commit": commit,
        "technical_status": technical,
        "decision": decision,
        "production_authorized": production_authorized,
        "promotion": {
            "mvp_version": MVP_VERSION,
            "tag": PROMOTION_TAG,
            "product_maturity": PRODUCT_MATURITY,
            "core_state": AUTHORIZED_CORE_STATE if production_authorized else PENDING_CORE_STATE,
            "operational_state": AUTHORIZED_CORE_STATE if production_authorized else PENDING_CORE_STATE,
            "scope": "SisTer Core",
            "recommendation": (
                f"create Git tag {PROMOTION_TAG} for SisTer Core {MVP_VERSION} as first controlled production MVP while retaining functional maturity {PRODUCT_MATURITY}"
                if production_authorized
                else "complete PROD-01 gates and formal authorization before tagging"
            ),
        },
        "gates": [asdict(g) for g in gates],
    }
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return payload


def write_promotion_artifacts(report_path: Path, core_state_path: Path, payload: dict) -> None:
    evidence = []
    for gate in payload["gates"]:
        for item in gate["evidence"]:
            if item not in evidence:
                evidence.append(item)

    lines = [
        "# PROD-01 Promotion Workflow",
        "",
        f"Commit: `{payload['commit']}`",
        f"Technical status: `{payload['technical_status']}`",
        f"Decision: `{payload['decision']}`",
        f"Production authorized: `{str(payload['production_authorized']).lower()}`",
        f"MVP version: `{payload['promotion']['mvp_version']}`",
        f"Recommended tag: `{payload['promotion']['tag']}`",
        f"Product maturity: `{payload['promotion']['product_maturity']}`",
        f"Core state: `{payload['promotion']['core_state']}`",
        f"Operational state: `{payload['promotion']['operational_state']}`",
        "",
        "## Gates",
        "",
    ]
    for gate in payload["gates"]:
        lines.append(f"- {gate['gate']} {gate['objective']}: `{gate['status']}` - {gate['detail']}")
    lines.extend(["", "## Evidências", ""])
    lines.extend(f"- `{item}`" for item in evidence)
    lines.extend(["", "## Recomendação", "", payload["promotion"]["recommendation"], ""])

    report_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    report_path.chmod(0o600)

    core_state = {
        "schema": "sister.core-production-state/1.0.0",
        "generated_at": payload["generated_at"],
        "commit": payload["commit"],
        "state": payload["promotion"]["core_state"],
        "mvp_version": payload["promotion"]["mvp_version"],
        "product_maturity": payload["promotion"]["product_maturity"],
        "operational_state": payload["promotion"]["operational_state"],
        "technical_status": payload["technical_status"],
        "production_authorized": payload["production_authorized"],
        "recommended_tag": payload["promotion"]["tag"],
    }
    core_state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    core_state_path.write_text(json.dumps(core_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    core_state_path.chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--promotion-report", type=Path, default=DEFAULT_PROMOTION_REPORT)
    parser.add_argument("--core-state", type=Path, default=DEFAULT_CORE_STATE)
    args = parser.parse_args()
    commit = git("rev-parse", "HEAD")
    gates = build_gates(commit)
    payload = write_report(args.report, gates, commit)
    write_promotion_artifacts(args.promotion_report, args.core_state, payload)
    print("SisTer PROD-01 Production Readiness Assessment")
    print("=" * 48)
    for gate in gates:
        print(f"{gate.gate} {gate.objective:<18} {gate.status:<20} {gate.detail}")
    print("=" * 48)
    print(f"Technical status ........ {payload['technical_status']}")
    print(f"Decision ................ {payload['decision']}")
    print(f"Production authorized ... {str(payload['production_authorized']).lower()}")
    print(f"MVP version ............. {payload['promotion']['mvp_version']}")
    print(f"Product maturity ........ {payload['promotion']['product_maturity']}")
    print(f"Core state .............. {payload['promotion']['core_state']}")
    print(f"Operational state ....... {payload['promotion']['operational_state']}")
    print(f"Recommended tag ......... {payload['promotion']['tag']}")
    print(f"Report .................. {args.report}")
    print(f"Promotion report ........ {args.promotion_report}")
    print(f"Core state report ....... {args.core_state}")
    return 0 if payload["technical_status"] == "READY" else 2


if __name__ == "__main__":
    sys.exit(main())
