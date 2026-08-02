#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
from pathlib import Path
import platform
import subprocess


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "packaging/haproxy/provenance.template.json"
SPEC = ROOT / "packaging/haproxy/haproxy.spec"
SPEC_RELATIVE = "packaging/haproxy/haproxy.spec"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(*command: str) -> str:
    return subprocess.run(
        command, check=True, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HAPROXY-RPM-01 provenance")
    parser.add_argument("--srpm", required=True, type=Path)
    parser.add_argument("--rpm", required=True, type=Path)
    parser.add_argument("--public-key", required=True, type=Path)
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--build-environment", required=True, type=Path)
    parser.add_argument("--installation-transaction-id", type=int)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    for path in (arguments.srpm, arguments.rpm, arguments.public_key,
                 arguments.build_environment, SPEC, TEMPLATE):
        if not path.is_file():
            parser.error(f"required file is absent: {path}")
    if len(arguments.fingerprint) < 40 or not all(
            character in "0123456789ABCDEFabcdef" for character in arguments.fingerprint):
        parser.error("a full OpenPGP fingerprint is required")
    fingerprint = arguments.fingerprint.upper()
    if len(fingerprint) != 40:
        parser.error("the OpenPGP fingerprint must contain exactly 40 hexadecimal characters")
    if subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", SPEC_RELATIVE],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=False).returncode != 0 or subprocess.run(
            ["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", SPEC_RELATIVE],
            check=False).returncode != 0:
        parser.error("commit the reviewed spec before generating provenance")

    public_key_details = run(
        "gpg", "--batch", "--show-keys", "--with-colons", str(arguments.public_key))
    public_fingerprints = [
        line.split(":")[9] for line in public_key_details.splitlines()
        if line.startswith("fpr:")]
    if not public_fingerprints or public_fingerprints[0].upper() != fingerprint:
        parser.error("public key and reviewed fingerprint do not match")
    rpm_signature = run(
        "rpm", "-qp", "--qf", "%{RSAHEADER:pgpsig}", str(arguments.rpm))
    if not rpm_signature or rpm_signature == "(none)":
        parser.error("binary RPM is not signed")
    if fingerprint[-16:].lower() not in rpm_signature.lower():
        parser.error("RPM signature does not identify the reviewed signing key")
    build_timestamp = datetime.fromtimestamp(
        int(run("rpm", "-qp", "--qf", "%{BUILDTIME}", str(arguments.rpm))),
        timezone.utc).isoformat()

    manifest = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    manifest.update({
        "spec_revision": run("git", "-C", str(ROOT), "rev-parse", "HEAD"),
        "spec_sha256": sha256(SPEC),
        "build_environment": arguments.build_environment.read_text(encoding="utf-8").strip(),
        "builder": getpass.getuser(),
        "build_host": f"{platform.system()} {platform.machine()}",
        "build_timestamp_utc": build_timestamp,
        "manifest_generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "signing_key_fingerprint": fingerprint,
        "public_key_sha256": sha256(arguments.public_key),
        "srpm": arguments.srpm.name,
        "srpm_sha256": sha256(arguments.srpm),
        "rpm": arguments.rpm.name,
        "rpm_sha256": sha256(arguments.rpm),
        "rpm_signature": rpm_signature,
    })
    if arguments.installation_transaction_id is not None:
        history = json.loads(run(
            "dnf", "history", "info", str(arguments.installation_transaction_id), "--json"))
        if len(history) != 1:
            parser.error("DNF did not return exactly one installation transaction")
        transaction = history[0]
        matching_packages = [
            package for package in transaction.get("packages", [])
            if package.get("action") == "Install"
            and package.get("nevra", "").startswith("sister-haproxy-lab-")]
        if transaction.get("status") != "Ok" or transaction.get("releasever") != "44":
            parser.error("DNF transaction is not a successful Fedora 44 transaction")
        if len(matching_packages) != 1:
            parser.error("DNF transaction does not install exactly one candidate package")
        installed_nevra = run(
            "rpm", "-q", "--qf", "%{NEVRA}", "sister-haproxy-lab")
        if installed_nevra != matching_packages[0]["nevra"].replace("-0:", "-", 1):
            parser.error("installed NEVRA differs from the DNF transaction")
        installed_verification = run("rpm", "-V", "sister-haproxy-lab")
        if installed_verification:
            parser.error("rpm -V reports modified installed files")
        installed_signature = run(
            "rpm", "-q", "--qf", "%{RSAHEADER:pgpsig}", "sister-haproxy-lab")
        if fingerprint[-16:].lower() not in installed_signature.lower():
            parser.error("installed package signature differs from the reviewed key")
        manifest.update({
            "installation_transaction_id": transaction["id"],
            "installation_status": transaction["status"],
            "installation_timestamp_utc": datetime.fromtimestamp(
                transaction["end_time"], timezone.utc).isoformat(),
            "installed_nevra": installed_nevra,
            "installed_rpm_verification": "PASS",
        })
    arguments.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = arguments.output.with_suffix(arguments.output.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(arguments.output)
    print(f"Provenance manifest: {arguments.output}")


if __name__ == "__main__":
    main()
