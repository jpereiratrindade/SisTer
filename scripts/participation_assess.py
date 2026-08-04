#!/usr/bin/env python3
"""Produce a technical participation assessment without authorizing anything."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "contracts/participation/1.0.0"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("contract")
    parser.add_argument("--commit", default="unrecorded")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    source = Path(args.contract)
    contract = json.loads(source.read_text(encoding="utf-8"))
    schema = json.loads((CONTRACT_DIR / "participation-contract.schema.json").read_text(encoding="utf-8"))
    schemas = {schema["$id"]: schema}
    for dependency in CONTRACT_DIR.glob("*.schema.json"):
        value = json.loads(dependency.read_text(encoding="utf-8"))
        schemas[value["$id"]] = value
    resolver = jsonschema.RefResolver.from_schema(schema, store=schemas)
    jsonschema.Draft202012Validator(schema, resolver=resolver).validate(contract)
    raw = json.dumps(contract, ensure_ascii=False, separators=(",", ":")).encode()
    assessment = {
        "schema": "sister.participation-assessment/1.0.0",
        "assessment_id": "assessment-technical-" + contract["participation_id"].removeprefix("part-"),
        "participation_id": contract["participation_id"],
        "contract_version": "1.0.0",
        "contract_digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "evaluated_commit": args.commit if len(args.commit) == 40 else "0" * 40,
        "profile_id": "participation-technical/1.0.0",
        "evaluator": {"id": "sge-participation", "version": "1.0.0"},
        "result": "PASS",
        "findings": [{"code": "participation.contract.valid", "layer": "existence", "explanation": "Contrato válido e permanece em proposed.", "evidence": ["evidence-participation-contract"]}],
        "evidence_used": ["evidence-participation-contract"], "evidence_missing": [],
        "confidence": 1, "limitations": ["Avaliação técnica não autoriza participação ou capacidade."],
        "gate_effect": "none", "recommendation": "Submeter à decisão humana competente.",
        "assessed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    print(json.dumps(assessment, ensure_ascii=False, indent=2) if args.json else f"{assessment['assessment_id']}: PASS — decisão humana ainda necessária")


if __name__ == "__main__":
    main()
