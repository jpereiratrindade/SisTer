#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / ".run" / "maturity" / "quality.json"
STEPS = [
    ("configure", "Configuração CMake", ["cmake", "-S", ".", "-B", "build"]),
    ("build", "Compilação", ["cmake", "--build", "build"]),
    ("ctest", "Testes CTest", ["ctest", "--test-dir", "build", "--output-on-failure"]),
    ("tool-contracts", "Contratos de ferramentas", ["python3", "scripts/validate_tool_contracts.py"]),
    ("governance", "Governança do repositório", ["python3", "scripts/validate_governance_repo.py"]),
    ("gateway-profile", "Perfil de segurança do gateway", ["python3", "scripts/validate_gateway_security_profile.py"]),
    ("local-resources", "Recursos locais", ["python3", "scripts/validate_local_resources.py"]),
    ("run-profiles", "Perfis de execução", ["python3", "scripts/resolve_run_profile.py", "--check"]),
    ("maturity-contracts", "Contratos de maturidade", ["python3", "scripts/maturity/validate-contracts.py"]),
    ("subsystems", "Testes de subsistemas", ["python3", "-m", "unittest", "scripts/subsystems/test_ensure.py"]),
    ("maturity-tests", "Testes do SGE e maturidade", ["python3", "-m", "unittest", "discover", "-s", "tests/maturity", "-p", "test_*.py"]),
    ("shell", "Validação de shell scripts", ["./scripts/validate_shell_scripts.sh"]),
]
GATEWAY_DYNAMIC_TESTS = [
    "gateway_protocol_tests",
    "gateway_header_sanitization_tests",
    "gateway_failure_tests",
    "gateway_abuse_tests",
    "gateway_slow_client_tests",
    "gateway_upstream_resilience_tests",
    "gateway_lab_tests",
]


def gateway_lab_available():
    raw = os.environ.get("GATEWAY_HAPROXY_BIN", "")
    binary = Path(raw)
    return (
        bool(raw)
        and binary.is_absolute()
        and binary.is_file()
        and os.access(binary, os.X_OK)
    )


def git_value(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def write_report(started_at, steps, result):
    finished_at = datetime.now(timezone.utc)
    payload = {
        "schema": "sister.quality-status/1.0.0",
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
        "result": result,
        "source": {
            "commit": git_value("rev-parse", "HEAD"),
            "short_commit": git_value("rev-parse", "--short=12", "HEAD"),
            "branch": git_value("branch", "--show-current"),
            "worktree": "dirty" if git_value("status", "--porcelain") else "clean",
        },
        "summary": {
            "total": len(steps),
            "passed": sum(step["status"] == "PASS" for step in steps),
            "failed": sum(step["status"] == "FAIL" for step in steps),
            "skipped": sum(step["status"] == "SKIP" for step in steps),
        },
        "steps": steps,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    temporary = REPORT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(REPORT)


def main():
    started_at = datetime.now(timezone.utc)
    steps = []
    failed = False
    for step_id, label, command in STEPS:
        if failed:
            steps.append({"id": step_id, "label": label, "command": command, "status": "SKIP", "duration_ms": 0, "exit_code": None})
            continue
        print(f"\n==> {label}", flush=True)
        started = time.monotonic()
        completed = subprocess.run(command, cwd=ROOT)
        duration_ms = round((time.monotonic() - started) * 1000)
        status = "PASS" if completed.returncode == 0 else "FAIL"
        record = {
            "id": step_id,
            "label": label,
            "command": command,
            "status": status,
            "duration_ms": duration_ms,
            "exit_code": completed.returncode,
        }
        if step_id == "ctest" and not gateway_lab_available():
            record["justified_skips"] = {
                "state": "SKIP_JUSTIFIED",
                "tests": GATEWAY_DYNAMIC_TESTS,
                "reason": "HAProxy 3.2.22+ real não foi configurado nesta execução local",
                "command": "GATEWAY_HAPROXY_BIN=/caminho/absoluto/haproxy ./scripts/run_quality.sh",
                "impact": "os controles dinâmicos do gateway não foram revalidados; skips são proibidos em SEC-03V",
            }
        steps.append(record)
        failed = completed.returncode != 0

    write_report(started_at, steps, "FAIL" if failed else "PASS")
    print(f"\nRelatório de qualidade: {REPORT.relative_to(ROOT)}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
