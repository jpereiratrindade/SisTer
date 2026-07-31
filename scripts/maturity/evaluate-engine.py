#!/usr/bin/env python3
import argparse
import copy
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from status_contract import atomic_write_json, validate_status


EXIT_GATE_FAILED = 1
EXIT_INVALID_CLI = 2
EXIT_INVALID_CONTRACT = 3
EXIT_EXECUTION_ERROR = 4
EXIT_ENGINE_DIVERGENCE = 5
STAGES = ("pre-alpha", "alpha", "beta", "gamma", "production")


def run_capture(command, cwd):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_or_exit(payload):
    errors = validate_status(payload)
    if errors:
        print("invalid maturity status: " + "; ".join(errors), file=sys.stderr)
        raise SystemExit(EXIT_INVALID_CONTRACT)


def write_payload(destination, payload):
    validate_or_exit(payload)
    if str(destination) == "-":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        atomic_write_json(destination, payload)


def result_code(payload):
    return 0 if payload.get("result") == "PASS" else EXIT_GATE_FAILED


def run_legacy(args, destination):
    with tempfile.NamedTemporaryFile(prefix="sge-legacy-", suffix=".json", delete=False) as handle:
        candidate = Path(handle.name)
    command = [
        str(args.repo / "scripts/verify-sister-maturity.sh"),
        "--stage",
        args.stage,
        "--repo",
        str(args.repo),
        "--engine",
        "legacy",
        "--status-json",
        str(candidate),
    ]
    if args.strict:
        command.append("--strict")
    proc = run_capture(command, args.repo)
    if not candidate.exists() or candidate.stat().st_size == 0:
        print(proc.stdout, end="")
        print(proc.stderr, end="", file=sys.stderr)
        print("legacy engine did not produce status JSON", file=sys.stderr)
        return EXIT_EXECUTION_ERROR
    payload = load_json(candidate)
    candidate.unlink(missing_ok=True)
    payload.setdefault("evaluation", {})
    payload["evaluation"].update({
        "engine": "legacy",
        "mode": "check",
        "engine_version": payload.get("verifier_version", "1.0.0"),
    })
    write_payload(destination, payload)
    return result_code(payload)


def run_declarative(args, destination):
    command = [
        sys.executable,
        str(args.repo / "scripts/maturity/evaluator.py"),
        "--repo",
        str(args.repo),
        "--component-root",
        str(args.component_root),
        "--profile",
        args.profile,
        "--stage",
        args.stage,
    ]
    if args.strict:
        command.append("--strict")
    proc = run_capture(command, args.repo)
    if proc.returncode not in (0, 1):
        print(proc.stdout, end="")
        print(proc.stderr, end="", file=sys.stderr)
        return EXIT_EXECUTION_ERROR
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        print(f"declarative engine produced invalid JSON: {exc}", file=sys.stderr)
        return EXIT_EXECUTION_ERROR
    payload.setdefault("evaluation", {})
    payload["evaluation"].update({
        "engine": "declarative",
        "mode": "check",
        "engine_version": payload.get("verifier_version", "1.0.0"),
    })
    write_payload(destination, payload)
    return result_code(payload)


def checks_by_id(payload):
    checks = {}
    for stage in payload.get("stages", []):
        for check in stage.get("checks", []):
            checks[check["id"]] = {
                "stage": stage["id"],
                "status": check["status"],
                "mandatory": check["mandatory"],
                "description": check["description"],
            }
    return checks


def add_divergence(divergences, path, classification, legacy, declarative, *, check_id=None, mandatory=False, blocking=True):
    item = {
        "path": path,
        "classification": classification,
        "legacy": legacy,
        "declarative": declarative,
        "blocking": blocking,
    }
    if check_id:
        item["check_id"] = check_id
        item["mandatory"] = bool(mandatory)
    divergences.append(item)


def compare_payloads(legacy, declarative):
    divergences = []
    if legacy.get("result") != declarative.get("result"):
        add_divergence(divergences, "result", "result_mismatch", legacy.get("result"), declarative.get("result"))
    if legacy.get("summary") != declarative.get("summary"):
        add_divergence(divergences, "summary", "summary_mismatch", legacy.get("summary"), declarative.get("summary"))
    if legacy.get("promotion") != declarative.get("promotion"):
        add_divergence(divergences, "promotion", "promotion_mismatch", legacy.get("promotion"), declarative.get("promotion"))

    legacy_checks = checks_by_id(legacy)
    declarative_checks = checks_by_id(declarative)
    for check_id in sorted(set(legacy_checks) | set(declarative_checks)):
        left = legacy_checks.get(check_id)
        right = declarative_checks.get(check_id)
        if left is None or right is None:
            add_divergence(
                divergences,
                f"checks.{check_id}",
                "check_missing",
                "missing" if left is None else left,
                "missing" if right is None else right,
                check_id=check_id,
                mandatory=(left or right or {}).get("mandatory", False),
            )
            continue
        for field in ("stage", "status", "mandatory"):
            if left[field] != right[field]:
                add_divergence(
                    divergences,
                    f"checks.{check_id}.{field}",
                    f"check_{field}_mismatch",
                    left[field],
                    right[field],
                    check_id=check_id,
                    mandatory=left.get("mandatory", False) or right.get("mandatory", False),
                )
    return divergences


def build_compare_payload(args, legacy, declarative, divergences):
    payload = copy.deepcopy(declarative)
    equivalent = not divergences
    blocking = any(item.get("blocking") for item in divergences)
    payload["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload["result"] = "FAIL" if blocking else declarative["result"]
    payload["promotion"] = {
        "applicable": True,
        "eligible": False if blocking else declarative["promotion"].get("eligible"),
        "recommendation": "block" if blocking else declarative["promotion"].get("recommendation", "block"),
    }
    if blocking:
        payload["next_actions"] = [
            "Investigar divergências entre legacy e declarative",
            f"Executar novamente o gate {args.stage} com --engine legacy",
            f"Executar novamente o gate {args.stage} com --engine declarative",
        ]
    payload["evaluation"] = {
        "engine": "compare",
        "mode": "check",
        "engine_version": payload.get("verifier_version", "1.0.0"),
        "requested_engine": "compare",
        "engines_executed": ["legacy", "declarative"],
        "comparison": {
            "performed": True,
            "equivalent": equivalent,
            "status": "EQUIVALENT" if equivalent else "DIVERGENT",
            "divergences": divergences[:100],
        },
    }
    return payload


def run_compare(args, destination):
    if args.component != "sister-core":
        print("compare engine is only available for sister-core in this increment", file=sys.stderr)
        return EXIT_INVALID_CLI
    with tempfile.NamedTemporaryFile(prefix="sge-legacy-", suffix=".json", delete=False) as left:
        legacy_path = Path(left.name)
    with tempfile.NamedTemporaryFile(prefix="sge-declarative-", suffix=".json", delete=False) as right:
        declarative_path = Path(right.name)

    run_legacy(args, legacy_path)
    run_declarative(args, declarative_path)
    legacy = load_json(legacy_path)
    declarative = load_json(declarative_path)
    legacy_path.unlink(missing_ok=True)
    declarative_path.unlink(missing_ok=True)

    divergences = compare_payloads(legacy, declarative)
    payload = build_compare_payload(args, legacy, declarative, divergences)
    write_payload(destination, payload)
    return EXIT_ENGINE_DIVERGENCE if divergences else result_code(payload)


def default_engine(component):
    return "compare" if component == "sister-core" else "declarative"


def main():
    parser = argparse.ArgumentParser(description="Evaluate a SGE maturity engine and write canonical status JSON.")
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--component-root", type=Path)
    parser.add_argument("--profile")
    parser.add_argument("--component", default="sister-core")
    parser.add_argument("--stage", required=True, choices=STAGES)
    parser.add_argument("--engine", choices=("legacy", "declarative", "compare"))
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    args.component_root = (args.component_root or args.repo).resolve()
    args.profile = args.profile or f"engineering/maturity/profiles/{args.component}.yaml"
    engine = args.engine or default_engine(args.component)

    destination = Path(args.status_json)
    if engine == "legacy":
        if args.component != "sister-core":
            print("legacy engine is only available for sister-core", file=sys.stderr)
            return EXIT_INVALID_CLI
        return run_legacy(args, destination)
    if engine == "declarative":
        return run_declarative(args, destination)
    return run_compare(args, destination)


if __name__ == "__main__":
    sys.exit(main())
