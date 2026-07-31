#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path

from status_contract import ABSOLUTE_PATH, SCHEMA, STAGES, atomic_write_json, validate_status


LABELS = {
    "pre-alpha": "Pré-Alfa",
    "alpha": "Alfa",
    "beta": "Beta",
    "gamma": "Gama",
    "production": "Produção",
}
RELATIVE_CANDIDATE = re.compile(r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+)")
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:authorization\s*:|(?:cookie|password|passwd|token|secret|api[_-]?key)\s*[=:])\s*[^\s,;]+"
)


def sanitize_text(value, repository, maximum):
    value = value.replace(repository, ".")
    value = "".join(character if ord(character) >= 0x20 else " " for character in value)
    value = SECRET_ASSIGNMENT.sub("[redacted]", value)
    value = ABSOLUTE_PATH.sub("[local-path]", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:maximum]


def evidence_paths(detail, repository):
    evidence = []
    root = Path(repository).resolve()
    for candidate in RELATIVE_CANDIDATE.findall(detail):
        if ".." in candidate.split("/"):
            continue
        path = (root / candidate).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            continue
        if path.is_file() and candidate not in evidence:
            evidence.append(candidate)
    return evidence[:20]


def build_payload(arguments):
    checks_by_stage = {stage: [] for stage in STAGES}
    blockers = []
    with open(arguments.results, encoding="utf-8", newline="") as source:
        for status, stage, check_id, mandatory, description, detail in csv.reader(source, delimiter="\t"):
            clean_description = sanitize_text(description, arguments.repository, 300)
            clean_detail = sanitize_text(detail, arguments.repository, 500)
            check = {
                "id": check_id,
                "status": status,
                "mandatory": mandatory == "yes",
                "description": clean_description,
                "detail": clean_detail,
                "evidence": evidence_paths(detail, arguments.repository),
            }
            checks_by_stage[stage].append(check)
            if status == "FAIL" and check["mandatory"]:
                blockers.append({
                    "stage": stage,
                    "id": check_id,
                    "description": clean_description,
                    "detail": clean_detail,
                })

    target_index = STAGES.index(arguments.target_stage)
    stages = []
    for index, stage_id in enumerate(STAGES):
        checks = checks_by_stage[stage_id]
        mandatory_failure = any(item["status"] == "FAIL" and item["mandatory"] for item in checks)
        if index > target_index:
            state = "not_started"
        elif mandatory_failure:
            state = "blocked"
        elif checks:
            state = "approved"
        else:
            state = "in_progress" if index == target_index else "not_started"
        stages.append({"id": stage_id, "label": LABELS[stage_id], "state": state, "checks": checks})

    actions = [f"Resolver o check obrigatório {item['id']}" for item in blockers[:5]]
    if blockers:
        actions.append(f"Executar novamente o gate {LABELS[arguments.target_stage]}")
    elif int(arguments.warned) > 0:
        actions = ["Revisar as advertências registradas", "Executar o gate em modo certify após consolidar o commit"]
    else:
        actions = ["Revisar as evidências e preparar a promoção do próximo estágio"]

    commit = arguments.commit if re.fullmatch(r"[0-9a-f]{40,64}", arguments.commit) else "unknown"
    short_commit = commit[:12] if commit != "unknown" else "unknown"
    
    payload = {
        "schema": SCHEMA,
        "project": "SisTer",
        "target_stage": arguments.target_stage,
        "result": arguments.result,
        "generated_at": arguments.generated_at,
        "verifier_version": arguments.verifier_version,
        "source": {
            "commit": commit,
            "short_commit": short_commit,
            "branch": sanitize_text(arguments.branch or "detached", arguments.repository, 128),
            "dirty": arguments.dirty == "true",
        },
        "summary": {
            "total": int(arguments.total),
            "passed": int(arguments.passed),
            "failed": int(arguments.failed),
            "warned": int(arguments.warned),
            "skipped": int(arguments.skipped),
            "mandatory_failures": int(arguments.mandatory_failures),
        },
        "stages": stages,
        "blockers": blockers[:100],
        "next_actions": actions,
        "attestation": {"available": False, "signed": False, "relative_path": None},
    }
    
    if arguments.engine:
        evaluation = {
            "engine": arguments.engine,
            "mode": arguments.engine_mode or "check",
        }
        if arguments.engine_version: evaluation["engine_version"] = arguments.engine_version
        if getattr(arguments, "model_id", None): evaluation["model_id"] = arguments.model_id
        if getattr(arguments, "model_version", None): evaluation["model_version"] = arguments.model_version
        if getattr(arguments, "profile_id", None): evaluation["profile_id"] = arguments.profile_id
        if getattr(arguments, "model_digest", None): evaluation["model_digest"] = arguments.model_digest
        if getattr(arguments, "profile_digest", None): evaluation["profile_digest"] = arguments.profile_digest
        
        if getattr(arguments, "compare_performed", None) == "true":
            evaluation["comparison"] = {
                "performed": True,
                "equivalent": getattr(arguments, "compare_equivalent", None) == "true"
            }
            
        payload["evaluation"] = evaluation
        
    return payload


def main():
    parser = argparse.ArgumentParser(description="Publish a sanitized SisTer maturity status")
    for name in (
        "results", "destination", "repository", "target-stage", "result", "generated-at",
        "verifier-version", "commit", "branch", "dirty", "total", "passed", "failed",
        "warned", "skipped", "mandatory-failures",
    ):
        parser.add_argument(f"--{name}", required=True)
    for name in (
        "engine", "engine-mode", "engine-version", "model-id", "model-version", "profile-id",
        "model-digest", "profile-digest", "compare-performed", "compare-equivalent",
    ):
        parser.add_argument(f"--{name}", required=False)
    arguments = parser.parse_args()
    payload = build_payload(arguments)
    errors = validate_status(payload)
    if errors:
        raise SystemExit("invalid generated maturity status: " + "; ".join(errors))
    atomic_write_json(arguments.destination, payload)


if __name__ == "__main__":
    main()
