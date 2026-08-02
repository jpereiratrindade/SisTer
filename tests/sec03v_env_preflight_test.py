#!/usr/bin/env python3
import json
from pathlib import Path
import shutil
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sec03v_env_preflight import Check, parse_environment, write_report  # noqa: E402


def main():
    temporary = Path(tempfile.mkdtemp(prefix="sec03v-preflight-"))
    try:
        environment = temporary / "sister.env"
        environment.write_text(
            "# candidate\nSISTER_DATABASE_URL=redacted-test-value\n"
            "SISTER_ENABLE_NEXO_SIGNED_INTEGRATION=true\n",
            encoding="utf-8",
        )
        values = parse_environment(environment)
        assert sorted(values) == [
            "SISTER_DATABASE_URL", "SISTER_ENABLE_NEXO_SIGNED_INTEGRATION"]

        environment.write_text("SISTER_ENV=production\nSISTER_ENV=dev\n", encoding="utf-8")
        try:
            parse_environment(environment)
        except ValueError as error:
            assert "duplicate variable" in str(error)
        else:
            raise AssertionError("duplicate environment assignment was accepted")

        report = temporary / "report.json"
        write_report(report, [Check("one", "PASS", "ok"), Check("two", "BLOCKED", "absent")])
        value = json.loads(report.read_text(encoding="utf-8"))
        assert value["schema"] == "sister.sec03v-env-preflight/1.0.0"
        assert value["result"] == "BLOCKED"
        assert stat.S_IMODE(report.stat().st_mode) == 0o600
        assert "redacted-test-value" not in report.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(temporary)

    print("sec03v_env_preflight_tests ok")


if __name__ == "__main__":
    main()
