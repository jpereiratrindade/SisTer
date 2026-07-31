#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import jsonschema
import yaml


DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate_document(path, schema, errors):
    try:
        data = load_yaml(path)
        jsonschema.Draft7Validator(schema).validate(data)
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        return None
    return data


def validate_check_suite(path, schema, errors):
    try:
        data = load_yaml(path)
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        return []
    if not isinstance(data, list):
        errors.append(f"{path}: check suite must be a YAML list")
        return []
    validator = jsonschema.Draft7Validator(schema)
    checks = []
    seen = set()
    for index, check in enumerate(data):
        label = f"{path}[{index}]"
        try:
            validator.validate(check)
        except Exception as exc:
            errors.append(f"{label}: {exc}")
            continue
        check_id = check.get("id")
        if check_id in seen:
            errors.append(f"{label}: duplicate check id {check_id}")
        seen.add(check_id)
        checks.append(check)
    return checks


def validate_profile_references(root, profile_path, profile, check_schema, errors):
    scripts = profile.get("scripts", {})
    for ref, script in scripts.items():
        script_path = script.get("path") if isinstance(script, dict) else None
        if not script_path:
            errors.append(f"{profile_path}: script {ref} must declare path")
            continue
        full_path = root / script_path
        if not full_path.exists():
            errors.append(f"{profile_path}: script {ref} path not found: {script_path}")

    mode = profile.get("evaluation_mode", "governed")
    governance_authority = profile.get("governance_authority", True)
    promotion_enabled = profile.get("promotion_enabled", True)
    if mode == "shadow" and (governance_authority or promotion_enabled):
        errors.append(f"{profile_path}: shadow requires governance_authority=false and promotion_enabled=false")
    if promotion_enabled and not governance_authority:
        errors.append(f"{profile_path}: promotion_enabled=true requires governance_authority=true")

    for suite in profile.get("check_suites", []):
        suite_path = root / suite
        if not suite_path.exists():
            errors.append(f"{profile_path}: check suite not found: {suite}")
            continue
        checks = validate_check_suite(suite_path, check_schema, errors)
        for check in checks:
            if check.get("type") == "script":
                script_ref = check.get("script_ref")
                if not script_ref:
                    errors.append(f"{suite_path}: script check {check.get('id')} must declare script_ref")
                elif script_ref not in scripts:
                    errors.append(f"{suite_path}: script check {check.get('id')} references unknown script {script_ref}")


def main():
    parser = argparse.ArgumentParser(description="Validate SGE maturity models, profiles and checks.")
    parser.add_argument("--repo", default=str(DEFAULT_ROOT), help="Repository root. Defaults to current SisTer checkout.")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    schema_paths = {
        "model": root / "contracts/engineering/maturity-model/1.0.0/manifest.schema.json",
        "profile": root / "contracts/engineering/maturity-profile/1.0.0/manifest.schema.json",
        "check": root / "contracts/engineering/maturity-check/1.0.0/manifest.schema.json",
    }
    schemas = {name: load_json(path) for name, path in schema_paths.items()}
    errors = []

    for path in sorted((root / "engineering/maturity/models").glob("*.yaml")):
        validate_document(path, schemas["model"], errors)

    profile_schema = schemas["profile"]
    check_schema = schemas["check"]
    for path in sorted((root / "engineering/maturity/profiles").glob("*.yaml")):
        profile = validate_document(path, profile_schema, errors)
        if profile:
            validate_profile_references(root, path, profile, check_schema, errors)

    if errors:
        print("maturity contract validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("maturity contract validation ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
