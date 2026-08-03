#!/usr/bin/env python3
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sec03v_env_preflight import (  # noqa: E402
    Check,
    healthy_sisterd_response,
    identity_key_pair_check,
    parse_environment,
    reference_contract_check,
    service_read_access_check,
    service_traverse_access_check,
    write_report,
)


def main():
    temporary = Path(tempfile.mkdtemp(prefix="sec03v-preflight-"))
    try:
        environment = temporary / "sister.env"
        environment.write_text(
            "# candidate\nSISTER_DATABASE_URL=redacted-test-value\n"
            "SISTER_ENABLE_REFERENCE_SUBSYSTEM=true\n",
            encoding="utf-8",
        )
        values = parse_environment(environment)
        assert sorted(values) == [
            "SISTER_DATABASE_URL", "SISTER_ENABLE_REFERENCE_SUBSYSTEM"]
        assert reference_contract_check().status == "PASS"

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

        private_key = temporary / "identity-private.pem"
        public_key = temporary / "identity-public.pem"
        other_private_key = temporary / "other-private.pem"
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "Ed25519", "-out", str(private_key)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["openssl", "pkey", "-in", str(private_key), "-pubout", "-out", str(public_key)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert identity_key_pair_check(private_key, public_key).status == "PASS"
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "Ed25519", "-out", str(other_private_key)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert identity_key_pair_check(other_private_key, public_key).status == "BLOCKED"

        service_access = service_read_access_check(
            "test.service_access", "account-that-does-not-exist", public_key)
        assert service_access.status == "BLOCKED"
        assert "service access" in service_access.detail or "cannot" in service_access.detail

        service_traversal = service_traverse_access_check(
            "test.service_traversal", "account-that-does-not-exist", temporary)
        assert service_traversal.status == "BLOCKED"
        assert "service access" in service_traversal.detail or "cannot" in service_traversal.detail

        healthy = (
            "verify return:1\nHTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            '{"status":"ok","service":"sisterd","database":"connected"}'
        )
        assert healthy_sisterd_response(healthy)
        assert not healthy_sisterd_response(healthy.replace("connected", "not_connected"))
        assert not healthy_sisterd_response(healthy.replace("200 OK", "503 Unavailable"))
    finally:
        shutil.rmtree(temporary)

    print("sec03v_env_preflight_tests ok")


if __name__ == "__main__":
    main()
