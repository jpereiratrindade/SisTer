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
QUALITY_REPORT = ROOT / ".run/maturity/quality.json"
ENV_EVIDENCE = ROOT / "docs/evidence/security/SEC-03V-ENV.md"
GATE_EVIDENCE = ROOT / "docs/evidence/security/SEC-03V.md"
SECURITY_PROFILE = ROOT / "ops/gateway/security-profile.json"


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


def build_gates() -> list[Gate]:
    return [
        quality_gate(),
        security_gate(),
        operational_evidence("G3", "Operação", "PROD-01-G3-operations.md", "reinício, reboot, atualização, certificado e logs"),
        operational_evidence("G4", "Recuperação", "PROD-01-G4-recovery.md", "backup/restauração, rollback e reinício de serviços"),
        operational_evidence("G5", "Observabilidade", "PROD-01-G5-observability.md", "health, métricas, logs, auditoria e carga"),
        Gate("G6", "Promoção", "AWAITING_AUTHORIZATION", "revisão formal de governança ainda necessária", ["docs/evidence/approval-template.md"]),
    ]


def write_report(path: Path, gates: list[Gate], commit: str) -> dict:
    technical = "BLOCKED" if any(g.status == "BLOCKED" for g in gates) else (
        "READY_FOR_PROMOTION" if all(g.status == "PASS" for g in gates) else "NOT_READY"
    )
    payload = {
        "schema": "sister.prod01-readiness/1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "commit": commit,
        "technical_status": technical,
        "decision": "AWAITING_AUTHORIZATION",
        "production_authorized": False,
        "gates": [asdict(g) for g in gates],
    }
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    commit = git("rev-parse", "HEAD")
    gates = build_gates()
    payload = write_report(args.report, gates, commit)
    print("SisTer PROD-01 Production Readiness Assessment")
    print("=" * 48)
    for gate in gates:
        print(f"{gate.gate} {gate.objective:<18} {gate.status:<20} {gate.detail}")
    print("=" * 48)
    print(f"Technical status ........ {payload['technical_status']}")
    print(f"Decision ................ {payload['decision']}")
    print("Production authorized ... false")
    print(f"Report .................. {args.report}")
    return 0 if payload["technical_status"] == "READY_FOR_PROMOTION" else 2


if __name__ == "__main__":
    sys.exit(main())
