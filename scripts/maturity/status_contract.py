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
        "next_actions", "attestation",
    }
    if not isinstance(payload, dict) or set(payload) != required:
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
