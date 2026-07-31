#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime
from pathlib import Path


SCHEMA = "sister.maturity-status/1.0.0"
HISTORY_SCHEMA = "sister.maturity-history/1.0.0"
STAGES = ("pre-alpha", "alpha", "beta", "gamma", "production")
CHECK_STATUSES = ("PASS", "FAIL", "WARN", "SKIP")
STAGE_STATES = ("approved", "in_progress", "blocked", "not_started")
MAX_STATUS_BYTES = 512 * 1024
RELATIVE_PATH = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9._/-]+$")
SECRET_VALUE = re.compile(
    r"(?i)(authorization\s*:|(?:cookie|password|passwd|token|secret|api[_-]?key)\s*[=:])"
)
ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z0-9_.:-])/(?:[A-Za-z0-9._-]+/)+[A-Za-z0-9._-]+|[A-Za-z]:\\"
)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_datetime(value):
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _safe_text(value, maximum, *, allow_empty=True):
    if not isinstance(value, str) or len(value) > maximum:
        return False
    if not allow_empty and not value:
        return False
    if any(ord(character) < 0x20 and character not in "\t\n\r" for character in value):
        return False
    return not SECRET_VALUE.search(value) and not ABSOLUTE_PATH.search(value)


def validate_status(payload):
    errors = []
    required = {
        "schema", "project", "target_stage", "result", "generated_at",
        "verifier_version", "source", "summary", "stages", "blockers",
        "next_actions", "attestation", "promotion",
    }
    if not isinstance(payload, dict):
        return ["status root fields do not match the contract"]
    
    actual_keys = set(payload)
    if not required.issubset(actual_keys) or not actual_keys.issubset(required | {"evaluation"}):
        return ["status root fields do not match the contract"]
    if payload["schema"] != SCHEMA:
        errors.append("unsupported status schema")
    if payload["project"] != "SisTer":
        errors.append("invalid project")
    if payload["target_stage"] not in STAGES:
        errors.append("invalid target_stage")
    if payload["result"] not in ("PASS", "FAIL"):
        errors.append("invalid result")
    if not _is_datetime(payload["generated_at"]):
        errors.append("invalid generated_at")
    if not _safe_text(payload["verifier_version"], 32, allow_empty=False):
        errors.append("invalid verifier_version")

    source = payload["source"]
    if not isinstance(source, dict) or set(source) != {"commit", "short_commit", "branch", "dirty"}:
        errors.append("invalid source")
    else:
        if not re.fullmatch(r"(?:[0-9a-f]{40,64}|unknown)", source["commit"] or ""):
            errors.append("invalid source commit")
        if not re.fullmatch(r"(?:[0-9a-f]{7,16}|unknown)", source["short_commit"] or ""):
            errors.append("invalid short commit")
        if not _safe_text(source["branch"], 128, allow_empty=False):
            errors.append("invalid branch")
        if not isinstance(source["dirty"], bool):
            errors.append("invalid dirty flag")

    summary = payload["summary"]
    summary_fields = {"total", "passed", "failed", "warned", "skipped", "mandatory_failures"}
    if not isinstance(summary, dict) or set(summary) != summary_fields or not all(
        _is_int(summary.get(field)) for field in summary_fields
    ):
        errors.append("invalid summary")

    promotion = payload["promotion"]
    if not isinstance(promotion, dict) or set(promotion) != {"applicable", "eligible", "recommendation"}:
        errors.append("invalid promotion block")
    else:
        if not isinstance(promotion["applicable"], bool):
            errors.append("invalid promotion applicable")
        if promotion["eligible"] is not None and not isinstance(promotion["eligible"], bool):
            errors.append("invalid promotion eligible")
        if promotion["recommendation"] not in ("promote", "block", "not_applicable"):
            errors.append("invalid promotion recommendation")

    stages = payload["stages"]
    if not isinstance(stages, list) or [item.get("id") for item in stages if isinstance(item, dict)] != list(STAGES):
        errors.append("stages must contain the five ordered stages")
    else:
        for stage in stages:
            if set(stage) != {"id", "label", "state", "checks"}:
                errors.append(f"invalid fields in stage {stage.get('id', '?')}")
                continue
            if not _safe_text(stage["label"], 40, allow_empty=False) or stage["state"] not in STAGE_STATES:
                errors.append(f"invalid stage metadata for {stage['id']}")
            if not isinstance(stage["checks"], list) or len(stage["checks"]) > 200:
                errors.append(f"invalid checks for {stage['id']}")
                continue
            for check in stage["checks"]:
                expected = {"id", "status", "mandatory", "description", "detail", "evidence"}
                if not isinstance(check, dict) or set(check) != expected:
                    errors.append(f"invalid check fields in {stage['id']}")
                    continue
                if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", check["id"] or ""):
                    errors.append("invalid check id")
                if check["status"] not in CHECK_STATUSES or not isinstance(check["mandatory"], bool):
                    errors.append(f"invalid check state for {check['id']}")
                if not _safe_text(check["description"], 300, allow_empty=False):
                    errors.append(f"unsafe check description for {check['id']}")
                if not _safe_text(check["detail"], 500):
                    errors.append(f"unsafe check detail for {check['id']}")
                if not isinstance(check["evidence"], list) or len(check["evidence"]) > 20 or not all(
                    isinstance(path, str) and len(path) <= 300 and RELATIVE_PATH.fullmatch(path)
                    for path in check["evidence"]
                ):
                    errors.append(f"invalid evidence for {check['id']}")

    blockers = payload["blockers"]
    if not isinstance(blockers, list) or len(blockers) > 100:
        errors.append("invalid blockers")
    else:
        for blocker in blockers:
            if not isinstance(blocker, dict) or set(blocker) != {"stage", "id", "description", "detail"}:
                errors.append("invalid blocker fields")
                continue
            if blocker["stage"] not in STAGES or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", blocker["id"] or ""):
                errors.append("invalid blocker identity")
            if not _safe_text(blocker["description"], 300, allow_empty=False) or not _safe_text(blocker["detail"], 500):
                errors.append(f"unsafe blocker {blocker['id']}")

    actions = payload["next_actions"]
    if not isinstance(actions, list) or len(actions) > 20 or not all(
        _safe_text(action, 300, allow_empty=False) for action in actions
    ):
        errors.append("invalid next_actions")

    attestation = payload["attestation"]
    if not isinstance(attestation, dict) or set(attestation) != {"available", "signed", "relative_path"}:
        errors.append("invalid attestation")
    else:
        if not isinstance(attestation["available"], bool) or not isinstance(attestation["signed"], bool):
            errors.append("invalid attestation flags")
        path = attestation["relative_path"]
        if path is not None and (not isinstance(path, str) or not RELATIVE_PATH.fullmatch(path)):
            errors.append("invalid attestation path")
    evaluation = payload.get("evaluation")
    if evaluation is not None:
        allowed = {
            "engine", "mode", "engine_version", "model_id", "model_version", "profile_id",
            "model_digest", "profile_digest", "evaluation_mode", "governance_authority",
            "promotion_enabled", "requested_engine", "engines_executed", "comparison",
        }
        if not isinstance(evaluation, dict) or not {"engine", "mode"}.issubset(evaluation) or not set(evaluation).issubset(allowed):
            errors.append("invalid evaluation fields")
        else:
            if evaluation["engine"] not in ("legacy", "declarative", "compare"):
                errors.append("invalid evaluation engine")
            if evaluation["mode"] not in ("check", "certify"):
                errors.append("invalid evaluation mode")
            if "requested_engine" in evaluation and evaluation["requested_engine"] not in ("legacy", "declarative", "compare"):
                errors.append("invalid requested engine")
            if "engines_executed" in evaluation and (
                not isinstance(evaluation["engines_executed"], list)
                or len(evaluation["engines_executed"]) > 3
                or not all(item in ("legacy", "declarative", "compare") for item in evaluation["engines_executed"])
            ):
                errors.append("invalid engines_executed")
            comparison = evaluation.get("comparison")
            if comparison is not None:
                allowed_comparison = {"performed", "equivalent", "status", "divergences"}
                if not isinstance(comparison, dict) or "performed" not in comparison or not set(comparison).issubset(allowed_comparison):
                    errors.append("invalid comparison")
                elif not isinstance(comparison["performed"], bool):
                    errors.append("invalid comparison performed")
                else:
                    if "equivalent" in comparison and not isinstance(comparison["equivalent"], bool):
                        errors.append("invalid comparison equivalent")
                    if "status" in comparison and comparison["status"] not in ("EQUIVALENT", "DIVERGENT"):
                        errors.append("invalid comparison status")
                    divergences = comparison.get("divergences", [])
                    if not isinstance(divergences, list) or len(divergences) > 100:
                        errors.append("invalid comparison divergences")
                    else:
                        for divergence in divergences:
                            required_divergence = {"path", "classification", "legacy", "declarative", "blocking"}
                            allowed_divergence = required_divergence | {"check_id", "mandatory"}
                            if not isinstance(divergence, dict) or not required_divergence.issubset(divergence) or not set(divergence).issubset(allowed_divergence):
                                errors.append("invalid divergence fields")
                                continue
                            if not _safe_text(divergence["path"], 160, allow_empty=False):
                                errors.append("invalid divergence path")
                            if not _safe_text(divergence["classification"], 80, allow_empty=False):
                                errors.append("invalid divergence classification")
                            if not isinstance(divergence["blocking"], bool):
                                errors.append("invalid divergence blocking")
                            if "check_id" in divergence and not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", divergence["check_id"] or ""):
                                errors.append("invalid divergence check_id")
                            if "mandatory" in divergence and not isinstance(divergence["mandatory"], bool):
                                errors.append("invalid divergence mandatory")
    return errors


def validate_history(payload):
    if not isinstance(payload, dict) or set(payload) != {"schema", "items"}:
        return ["history root fields do not match the contract"]
    errors = []
    if payload["schema"] != HISTORY_SCHEMA:
        errors.append("unsupported history schema")
    items = payload["items"]
    if not isinstance(items, list) or len(items) > 100:
        return errors + ["invalid history items"]
    expected = {"generated_at", "target_stage", "result", "short_commit", "passed", "failed", "warned", "relative_path"}
    for item in items:
        if not isinstance(item, dict) or set(item) != expected:
            errors.append("invalid history item fields")
            continue
        if not _is_datetime(item["generated_at"]) or item["target_stage"] not in STAGES or item["result"] not in ("PASS", "FAIL"):
            errors.append("invalid history item metadata")
        if not re.fullmatch(r"(?:[0-9a-f]{7,16}|unknown)", item["short_commit"] or ""):
            errors.append("invalid history commit")
        if not all(_is_int(item[field]) for field in ("passed", "failed", "warned")):
            errors.append("invalid history counts")
        if not re.fullmatch(r"history/[A-Za-z0-9._-]+\.json", item["relative_path"] or ""):
            errors.append("invalid history path")
    return errors


def load_json(path, maximum=MAX_STATUS_BYTES):
    source = Path(path)
    if source.stat().st_size > maximum:
        raise ValueError("JSON exceeds size limit")
    return json.loads(source.read_text(encoding="utf-8"))


def atomic_write_json(path, payload):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
