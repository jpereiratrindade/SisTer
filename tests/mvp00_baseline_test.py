#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "engineering/baselines/mvp-00.json"


def main() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert baseline["schema"] == "sister.engineering.baseline/1.0.0"
    assert baseline["operational_authorization"] is False
    assert baseline["g6_authorized"] is False
    assert baseline["contract_freeze"] == "mvp-01"
    assert baseline["domain_prototypes"] == {
        "IntegrationRun": "TESTADO_EM_MEMORIA",
        "GovernedSystemRegistry": "TESTADO_EM_MEMORIA",
    }
    assert len(baseline["source_commit"]) == 40
    for artifact in baseline["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.is_file(), artifact["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == artifact["sha256"], f"frozen baseline changed: {artifact['path']}"
    print("mvp00 baseline validation ok")


if __name__ == "__main__":
    main()
