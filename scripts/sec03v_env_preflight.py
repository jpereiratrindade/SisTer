#!/usr/bin/env python3
"""Fail-closed host preflight for the SEC-03V candidate environment."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import grp
import json
import os
from pathlib import Path
import pwd
import re
import socket
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / ".run/security/sec03v-env-preflight.json"
NON_INTERACTIVE_SHELLS = {"/bin/false", "/sbin/nologin", "/usr/sbin/nologin"}
REQUIRED_ENVIRONMENT = {
    "SISTER_DATABASE_URL",
    "SISTER_ENABLE_NEXO_SIGNED_INTEGRATION",
    "SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE",
    "SISTER_INTERNAL_IDENTITY_KEY_ID",
    "SISTER_INTERNAL_IDENTITY_TTL_SECONDS",
    "SISTER_WEB_ROOT",
    "SISTER_MATURITY_ROOT",
}


@dataclass(frozen=True)
class Check:
    control: str
    status: str
    detail: str


def execute(command: list[str], timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )


def file_identity(path: Path) -> tuple[str, str, int, int]:
    metadata = path.lstat()
    return (
        pwd.getpwuid(metadata.st_uid).pw_name,
        grp.getgrgid(metadata.st_gid).gr_name,
        stat.S_IMODE(metadata.st_mode),
        metadata.st_mode,
    )


def parse_environment(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"invalid assignment at line {number}")
        name, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
            raise ValueError(f"invalid variable name at line {number}")
        if name in values:
            raise ValueError(f"duplicate variable {name}")
        values[name] = value
    return values


def account_check(name: str, expected_group: str | None = None) -> Check:
    try:
        account = pwd.getpwnam(name)
        primary_group = grp.getgrgid(account.pw_gid).gr_name
    except KeyError:
        return Check(f"account.{name}", "BLOCKED", "account is absent")
    if account.pw_shell not in NON_INTERACTIVE_SHELLS:
        return Check(f"account.{name}", "BLOCKED", "account has an interactive shell")
    if expected_group and primary_group != expected_group:
        return Check(
            f"account.{name}", "BLOCKED", f"primary group must be {expected_group}")
    return Check(f"account.{name}", "PASS", "non-interactive service account")


def gateway_group_check() -> Check:
    try:
        gateway_group = grp.getgrnam("haproxy")
        gateway = pwd.getpwnam("sister-gateway")
    except KeyError:
        return Check("group.haproxy", "BLOCKED", "group or sister-gateway account is absent")
    members = set(gateway_group.gr_mem)
    if grp.getgrgid(gateway.pw_gid).gr_name == "haproxy":
        members.add("sister-gateway")
    if "sister-gateway" not in members:
        return Check("group.haproxy", "BLOCKED", "sister-gateway is not a member")
    interactive = []
    for name in sorted(members):
        try:
            account = pwd.getpwnam(name)
        except KeyError:
            continue
        if account.pw_uid >= 1000 and account.pw_shell not in NON_INTERACTIVE_SHELLS:
            interactive.append(name)
    if interactive:
        return Check("group.haproxy", "BLOCKED", "interactive users belong to the group")
    return Check("group.haproxy", "PASS", "membership is restricted to service identities")


def governed_file(
    control: str,
    path: Path,
    owner: str,
    group: str,
    maximum_mode: int,
    *,
    file_type: str = "file",
) -> Check:
    try:
        actual_owner, actual_group, mode, raw_mode = file_identity(path)
    except (FileNotFoundError, KeyError, OSError):
        return Check(control, "BLOCKED", f"{path} is absent or unreadable")
    type_ok = stat.S_ISREG(raw_mode) if file_type == "file" else stat.S_ISDIR(raw_mode)
    if path.is_symlink() or not type_ok:
        return Check(control, "BLOCKED", f"{path} has an invalid file type")
    if actual_owner != owner or actual_group != group or mode & ~maximum_mode:
        return Check(
            control,
            "BLOCKED",
            f"{path} requires {owner}:{group} mode no broader than {maximum_mode:04o}",
        )
    return Check(control, "PASS", f"{path} ownership and mode are governed")


def installed_file_check(control: str, source: Path, installed: Path) -> Check:
    try:
        if source.read_bytes() != installed.read_bytes():
            return Check(control, "BLOCKED", "installed file differs from revision")
    except OSError:
        return Check(control, "BLOCKED", "installed file is absent or unreadable")
    return Check(control, "PASS", "installed file matches the repository")


def installed_unit_check(name: str) -> Check:
    return installed_file_check(
        f"unit.{name}.content",
        ROOT / "ops/systemd" / name,
        Path("/etc/systemd/system") / name,
    )


def installed_revision_check() -> Check:
    path = Path("/opt/sister/.sister-revision")
    identity = governed_file("installation.revision", path, "root", "root", 0o444)
    if identity.status != "PASS":
        return identity
    try:
        installed = path.read_text(encoding="ascii").strip()
        current = execute(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).stdout.strip()
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        return Check("installation.revision", "BLOCKED", "installed revision could not be verified")
    valid = bool(re.fullmatch(r"[0-9a-f]{40}", installed)) and installed == current
    return Check(
        "installation.revision", "PASS" if valid else "BLOCKED",
        "installed revision matches the worktree" if valid else "installed revision differs from the worktree",
    )


def systemd_state(name: str, state: str) -> Check:
    command = "is-enabled" if state == "enabled" else "is-active"
    try:
        result = execute(["systemctl", command, name])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return Check(f"unit.{name}.{state}", "BLOCKED", "systemctl is unavailable")
    if result.returncode != 0 or result.stdout.strip() != state:
        return Check(f"unit.{name}.{state}", "BLOCKED", f"unit is not {state}")
    return Check(f"unit.{name}.{state}", "PASS", f"unit is {state}")


def environment_check() -> list[Check]:
    path = Path("/etc/sister/sister.env")
    checks = [governed_file("config.sister", path, "root", "root", 0o600)]
    if checks[0].status != "PASS":
        return checks
    try:
        values = parse_environment(path)
    except (OSError, UnicodeError, ValueError) as error:
        return checks + [Check("config.sister.contract", "BLOCKED", str(error))]
    missing = sorted(REQUIRED_ENVIRONMENT - values.keys())
    valid = not missing
    valid &= values.get("SISTER_ENABLE_NEXO_SIGNED_INTEGRATION", "").lower() == "true"
    valid &= values.get("SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE") == (
        "/etc/sister/identity-private.pem"
    )
    valid &= values.get("SISTER_WEB_ROOT") == "/opt/sister/web"
    valid &= values.get("SISTER_MATURITY_ROOT") == "/var/lib/sister/maturity"
    try:
        ttl = int(values.get("SISTER_INTERNAL_IDENTITY_TTL_SECONDS", "0"))
        valid &= 1 <= ttl <= 300
    except ValueError:
        valid = False
    detail = "required variables are present and candidate integration is enabled"
    if not valid:
        detail = "required variables are missing or violate the candidate contract"
    return checks + [Check("config.sister.contract", "PASS" if valid else "BLOCKED", detail)]


def socket_checks() -> list[Check]:
    checks = [
        governed_file("runtime.directory", Path("/run/sister"), "root", "haproxy", 0o750, file_type="directory")
    ]
    path = Path("/run/sister/sisterd.sock")
    try:
        owner, group, mode, raw_mode = file_identity(path)
        valid = stat.S_ISSOCK(raw_mode) and owner == "sister" and group == "haproxy" and mode == 0o660
    except (FileNotFoundError, KeyError, OSError):
        valid = False
    detail = "Unix listener is sister:haproxy mode 0660" if valid else "governed Unix listener is absent or invalid"
    checks.append(Check("runtime.socket", "PASS" if valid else "BLOCKED", detail))
    return checks


def no_tcp_listener() -> Check:
    try:
        result = execute(["ss", "-ltnH"])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return Check("transport.no_sisterd_tcp", "BLOCKED", "ss is unavailable")
    found = any(re.search(r"(?:^|:)8000$", column) for line in result.stdout.splitlines() for column in line.split())
    return Check(
        "transport.no_sisterd_tcp",
        "BLOCKED" if found else "PASS",
        "TCP port 8000 is listening" if found else "TCP port 8000 is absent",
    )


def haproxy_checks(binary: Path) -> list[Check]:
    checks: list[Check] = []
    if not binary.is_absolute() or not binary.is_file() or not os.access(binary, os.X_OK):
        return [Check("gateway.binary", "BLOCKED", "absolute executable HAProxy binary is absent")]
    try:
        with binary.open("rb") as stream:
            is_native_binary = stream.read(4) == b"\x7fELF"
    except OSError:
        is_native_binary = False
    if not is_native_binary:
        return [Check("gateway.binary", "BLOCKED", "candidate requires a native HAProxy executable")]
    try:
        version = execute([str(binary), "-vv"]).stdout
    except (OSError, subprocess.TimeoutExpired):
        version = ""
    match = re.search(r"HAProxy version (3\.2\.(\d+))", version)
    valid_version = bool(match and int(match.group(2)) >= 22)
    checks.append(Check(
        "gateway.binary", "PASS" if valid_version else "BLOCKED",
        f"HAProxy {match.group(1)}" if valid_version and match else "HAProxy 3.2.22+ is required",
    ))
    config = Path("/etc/sister/gateway/haproxy.cfg")
    checks.append(governed_file("gateway.config", config, "root", "sister-gateway", 0o640))
    checks.append(governed_file(
        "gateway.certificate", Path("/etc/sister/gateway/tls.pem"),
        "root", "sister-gateway", 0o640,
    ))
    if checks[-1].status == "PASS":
        try:
            certificate = execute([
                "openssl", "x509", "-in", "/etc/sister/gateway/tls.pem", "-noout",
                "-checkend", "3600", "-checkhost", "sister-gateway.test",
            ])
            certificate_valid = certificate.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            certificate_valid = False
        checks.append(Check(
            "gateway.certificate.validity",
            "PASS" if certificate_valid else "BLOCKED",
            "certificate is valid for the candidate Host" if certificate_valid
            else "certificate is expired, near expiry, or has the wrong Host",
        ))
    if all(check.status == "PASS" for check in checks):
        result = execute([str(binary), "-c", "-V", "-f", str(config)])
        checks.append(Check(
            "gateway.config.offline", "PASS" if result.returncode == 0 else "BLOCKED",
            "configuration accepted offline" if result.returncode == 0 else "configuration rejected offline",
        ))
    return checks


def nexo_check() -> Check:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8015/api/health", timeout=2) as response:
            value = json.load(response)
        valid = response.status == 200 and value.get("status") == "ok" and (
            value.get("service") == "sister-nexo" and value.get("database") == "ok"
        )
    except (OSError, ValueError, urllib.error.URLError):
        valid = False
    return Check(
        "nexo.readiness", "PASS" if valid else "BLOCKED",
        "Nexo and PostgreSQL are READY" if valid else "Nexo readiness contract failed",
    )


def worktree_check(path: Path, name: str) -> Check:
    try:
        result = execute(["git", "-C", str(path), "status", "--porcelain"])
        revision = execute(["git", "-C", str(path), "rev-parse", "HEAD"])
    except (OSError, subprocess.TimeoutExpired):
        return Check(f"revision.{name}", "BLOCKED", "Git state could not be read")
    valid = result.returncode == 0 and not result.stdout.strip() and revision.returncode == 0
    detail = f"clean revision {revision.stdout.strip()}" if valid else "worktree is dirty or unknown"
    return Check(f"revision.{name}", "PASS" if valid else "BLOCKED", detail)


def write_report(path: Path, checks: list[Check]) -> None:
    result = "READY" if all(check.status == "PASS" for check in checks) else "BLOCKED"
    payload = {
        "schema": "sister.sec03v-env-preflight/1.0.0",
        "result": result,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "checks": [asdict(check) for check in checks],
    }
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary_name, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--haproxy-bin", type=Path, default=Path("/usr/local/sbin/haproxy-3.2.22"))
    parser.add_argument("--nexo-root", type=Path, default=ROOT.parent / "sister-nexo")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    arguments = parser.parse_args()

    checks = [
        worktree_check(ROOT, "sister"),
        worktree_check(arguments.nexo_root, "nexo"),
        account_check("sister", "sister"),
        account_check("sister-gateway"),
        gateway_group_check(),
        governed_file("installation.binary", Path("/opt/sister/build/apps/sisterd/sisterd"), "root", "root", 0o755),
        governed_file("installation.web", Path("/opt/sister/web"), "root", "root", 0o755, file_type="directory"),
        installed_revision_check(),
        installed_unit_check("sisterd.socket"),
        installed_unit_check("sisterd.service"),
        installed_file_check(
            "tmpfiles.sister.content",
            ROOT / "ops/tmpfiles.d/sister.conf",
            Path("/etc/tmpfiles.d/sister.conf"),
        ),
        systemd_state("sisterd.socket", "enabled"),
        systemd_state("sisterd.socket", "active"),
    ]
    checks.extend(environment_check())
    checks.extend([
        governed_file(
            "identity.private_key", Path("/etc/sister/identity-private.pem"),
            "sister", "sister", 0o600,
        ),
        governed_file(
            "identity.public_key", Path("/etc/sister/identity-public.pem"),
            "root", "root", 0o644,
        ),
    ])
    checks.extend(socket_checks())
    checks.append(no_tcp_listener())
    checks.extend(haproxy_checks(arguments.haproxy_bin))
    checks.append(nexo_check())

    write_report(arguments.report, checks)
    result = "READY" if all(check.status == "PASS" for check in checks) else "BLOCKED"
    for check in checks:
        print(f"{check.status:7} {check.control}: {check.detail}")
    print(f"SEC-03V-ENV: {result}")
    print(f"Report: {arguments.report}")
    return 0 if result == "READY" else 2


if __name__ == "__main__":
    sys.exit(main())
