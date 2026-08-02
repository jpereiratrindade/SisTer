#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "packaging/haproxy"
EXPECTED_SHA256 = "afca3a26d573df53d0e1fc475dcd743ec5875e038e1476c80e871d70228ca2da"


def main():
    spec = (PACKAGE_ROOT / "haproxy.spec").read_text(encoding="utf-8")
    checksum = (PACKAGE_ROOT / "sources/haproxy-3.2.22.tar.gz.sha256").read_text(
        encoding="ascii").strip()
    template = json.loads((PACKAGE_ROOT / "provenance.template.json").read_text(encoding="utf-8"))
    build_script = (ROOT / "scripts/packaging/build_haproxy_rpm.sh").read_text(encoding="utf-8")
    sign_script = (ROOT / "scripts/packaging/sign_haproxy_rpms.sh").read_text(encoding="utf-8")
    source_script = (ROOT / "scripts/packaging/prepare_haproxy_source.sh").read_text(encoding="utf-8")
    public_key = PACKAGE_ROOT / "keys/sister-sec03v-rpm-signing.asc"
    evidence = json.loads((ROOT / "docs/evidence/security/HAPROXY-RPM-01.json").read_text(
        encoding="utf-8"))

    assert checksum == f"{EXPECTED_SHA256}  haproxy-3.2.22.tar.gz"
    assert re.search(r"^Name:\s+sister-haproxy-lab$", spec, re.MULTILINE)
    assert re.search(r"^Version:\s+3\.2\.22$", spec, re.MULTILINE)
    assert "USE_SYSTEMD=1" not in spec
    assert "systemd-devel" not in spec
    assert "-Ws master-worker mode with systemd notify support." in spec
    assert "USE_OPENSSL=1" in spec
    assert "USE_PCRE2=1" in spec
    assert "BuildRequires:  libxcrypt-devel" in spec
    assert "/usr/local/sbin/haproxy-%{version}" in spec
    assert "%doc CHANGELOG README.md INSTALL" in spec
    for forbidden in ("podman", "docker", "curl", "wget", "%post", "%preun", "%postun"):
        assert forbidden not in spec.lower(), forbidden
    assert "sister-gateway.service" not in spec

    assert template["schema"] == "sister.haproxy-rpm-provenance/1.0.0"
    assert template["upstream_sha256"] == EXPECTED_SHA256
    assert template["version"] == "3.2.22"
    assert template["installation_manager"] == "dnf"
    assert "registry.fedoraproject.org/fedora:44" in build_script
    assert "podman run" in build_script
    assert "GNUPGHOME" in sign_script
    assert "HAPROXY_SIGNING_FINGERPRINT" in sign_script
    assert '"_keyring fs"' in sign_script
    assert "verification_keyring" in sign_script
    assert "GOVERNED_PUBLIC_KEY" in sign_script
    assert 'CHECKSUM_URL="${SOURCE_URL}.sha256"' in source_script
    assert "published_sha256" in source_script
    assert evidence["signing_key_fingerprint"] == "ED3F4CE4C756983F211097B6AB5D893C71F31D65"
    assert evidence["public_key_sha256"] == hashlib.sha256(public_key.read_bytes()).hexdigest()
    assert evidence["rpm_signature"].endswith("Key ID ab5d893c71f31d65")
    assert evidence["installation_transaction_id"] == 135
    assert evidence["installation_status"] == "Ok"
    assert evidence["installed_rpm_verification"] == "PASS"

    key_details = subprocess.run(
        ["gpg", "--batch", "--show-keys", "--with-colons", str(public_key)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        check=True,
    ).stdout
    fingerprints = [
        line.split(":")[9] for line in key_details.splitlines()
        if line.startswith("fpr:")]
    assert fingerprints[0] == evidence["signing_key_fingerprint"]

    parsed = subprocess.run(
        ["rpmspec", "-P", str(PACKAGE_ROOT / "haproxy.spec")],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=10,
        check=False,
    )
    assert parsed.returncode == 0, parsed.stdout
    assert "sister-haproxy-lab" in parsed.stdout
    print("haproxy_packaging_tests ok")


if __name__ == "__main__":
    main()
