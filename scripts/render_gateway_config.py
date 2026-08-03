#!/usr/bin/env python3
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "ops/gateway/security-profile.json"
TEMPLATE_PATH = ROOT / "ops/gateway/haproxy/haproxy.cfg.in"
RUN_ROOT = ROOT / ".run/gateway"
DEFAULT_OUTPUT = RUN_ROOT / "haproxy.cfg"
CANDIDATE_CONFIG = Path("/etc/sister/gateway/haproxy.cfg")
CANDIDATE_TLS_PEM = Path("/etc/sister/gateway/tls.pem")
CANDIDATE_ERROR_ROOT = Path("/etc/sister/gateway/errors")
CANDIDATE_STATS_SOCKET = Path("/run/sister-gateway/haproxy.sock")
CANDIDATE_UPSTREAM_SOCKET = Path("/run/sister/sisterd.sock")

sys.path.insert(0, str(ROOT / "scripts"))
from validate_gateway_security_profile import load_json, validate_profile  # noqa: E402


PLACEHOLDER = re.compile(r"@@[A-Z0-9_]+@@")
HOST = re.compile(r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+")
SAFE_PATH = re.compile(r"[A-Za-z0-9_./-]+")
FORBIDDEN_CONFIG = (
    re.compile(r"^\s*lua-load\b", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*filter\s+lua\b", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*resolvers\b", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*server-template\b", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*http-request\s+set-dst(?:-port)?\b", re.MULTILINE | re.IGNORECASE),
)


class RenderError(RuntimeError):
    pass


def require_absolute_safe_path(raw, name, *, must_exist=False, executable=False):
    path = Path(raw)
    if not path.is_absolute() or not SAFE_PATH.fullmatch(raw):
        raise RenderError(f"{name} must be an absolute path without whitespace")
    if must_exist and not path.is_file():
        raise RenderError(f"{name} must reference a regular file")
    if executable and not os.access(path, os.X_OK):
        raise RenderError(f"{name} must be executable")
    return path


def lab_run_root(environment):
    raw = environment.get("GATEWAY_RUN_ROOT")
    if not raw:
        return RUN_ROOT.resolve()
    path = Path(raw)
    if not path.is_absolute() or not SAFE_PATH.fullmatch(raw):
        raise RenderError("GATEWAY_RUN_ROOT must be an absolute path without whitespace")
    resolved = path.resolve()
    allowed = (ROOT / ".run").resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise RenderError(f"GATEWAY_RUN_ROOT must remain inside {allowed}")
    return resolved


def require_inside_run_root(path, name, run_root=None):
    resolved_parent = path.parent.resolve()
    run_root = (run_root or RUN_ROOT).resolve()
    if resolved_parent != run_root and run_root not in resolved_parent.parents:
        raise RenderError(f"{name} must remain inside {run_root}")


def require_private_file(path, name, maximum_mode=0o600):
    if path.is_symlink() or not path.is_file():
        raise RenderError(f"{name} must be a regular non-symlink file")
    permissions = stat.S_IMODE(path.stat().st_mode)
    if permissions & ~maximum_mode:
        raise RenderError(f"{name} permissions must be {maximum_mode:04o} or stricter")


def haproxy_version(binary):
    completed = subprocess.run(
        [str(binary), "-vv"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=10,
        check=False,
    )
    match = re.search(r"HAProxy version\s+(\d+)\.(\d+)\.(\d+)", completed.stdout)
    if completed.returncode != 0 or not match:
        raise RenderError("could not verify HAProxy version")
    major, minor, patch = (int(value) for value in match.groups())
    if (major, minor) != (3, 2) or patch < 22:
        raise RenderError("HAProxy must be version 3.2.22 or newer in the 3.2 branch")
    return f"{major}.{minor}.{patch}"


def checked_environment(environment, scope="lab"):
    if scope not in {"lab", "lan-lab", "candidate"}:
        raise RenderError(f"unsupported gateway scope: {scope}")
    required = {
        "GATEWAY_TLS_PEM",
        "GATEWAY_ALLOWED_HOST",
        "GATEWAY_CANONICAL_HOST",
        "GATEWAY_HAPROXY_BIN",
    }
    missing = sorted(name for name in required if not environment.get(name))
    if missing:
        raise RenderError("missing environment: " + ", ".join(missing))
    forbidden_tcp = sorted(
        name for name in ("GATEWAY_UPSTREAM_ADDRESS", "GATEWAY_UPSTREAM_PORT")
        if environment.get(name)
    )
    if forbidden_tcp:
        raise RenderError("TCP upstream configuration is forbidden: " + ", ".join(forbidden_tcp))

    run_root = lab_run_root(environment)
    values = {
        "GATEWAY_TLS_PEM": environment["GATEWAY_TLS_PEM"],
        "GATEWAY_ALLOWED_HOST": environment["GATEWAY_ALLOWED_HOST"].lower(),
        "GATEWAY_CANONICAL_HOST": environment["GATEWAY_CANONICAL_HOST"].lower(),
        "GATEWAY_LISTEN_ADDRESS": environment.get("GATEWAY_LISTEN_ADDRESS", "127.0.0.1"),
        "GATEWAY_LISTEN_PORT": environment.get("GATEWAY_LISTEN_PORT", "8443"),
        "GATEWAY_UPSTREAM_SOCKET": environment.get(
            "GATEWAY_UPSTREAM_SOCKET", str((run_root / "sisterd.sock").resolve())),
        "GATEWAY_ERROR_ROOT": str((ROOT / "ops/gateway/haproxy/errors").resolve()),
        "GATEWAY_STATS_SOCKET": str((run_root / "haproxy.sock").resolve()),
    }
    try:
        listen_address = ipaddress.ip_address(values["GATEWAY_LISTEN_ADDRESS"])
    except ValueError as exc:
        raise RenderError(f"{scope} listener must be an IPv4 address") from exc
    if listen_address.version != 4:
        raise RenderError(f"{scope} listener must be an IPv4 address")
    if scope in {"lab", "candidate"} and values["GATEWAY_LISTEN_ADDRESS"] != "127.0.0.1":
        raise RenderError(f"{scope} listener must be 127.0.0.1")
    if scope == "lan-lab":
        private_networks = (
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        )
        if not any(listen_address in network for network in private_networks):
            raise RenderError("lan-lab listener must be an explicit private IPv4 address")
    if values["GATEWAY_LISTEN_PORT"] != "8443":
        raise RenderError(f"{scope} listener port must be 8443")
    upstream_socket = require_absolute_safe_path(
        values["GATEWAY_UPSTREAM_SOCKET"], "GATEWAY_UPSTREAM_SOCKET")
    if scope in {"lab", "lan-lab"}:
        require_inside_run_root(upstream_socket, "GATEWAY_UPSTREAM_SOCKET", run_root)
        if upstream_socket != (run_root / "sisterd.sock").resolve():
            raise RenderError("laboratory upstream must use the governed runtime Unix socket")
    elif upstream_socket != CANDIDATE_UPSTREAM_SOCKET:
        raise RenderError("candidate upstream must use /run/sister/sisterd.sock")
    allowed_host = values["GATEWAY_ALLOWED_HOST"]
    if not HOST.fullmatch(allowed_host) or "*" in allowed_host or not allowed_host.endswith(".test"):
        raise RenderError(f"{scope} Host must be one exact DNS name under .test")
    if values["GATEWAY_CANONICAL_HOST"] != allowed_host:
        raise RenderError(f"canonical and allowed {scope} Host must match")

    pem = require_absolute_safe_path(values["GATEWAY_TLS_PEM"], "GATEWAY_TLS_PEM", must_exist=True)
    if scope in {"lab", "lan-lab"}:
        require_inside_run_root(pem, "GATEWAY_TLS_PEM", run_root)
        require_private_file(pem, "GATEWAY_TLS_PEM")
    else:
        if pem != CANDIDATE_TLS_PEM:
            raise RenderError("candidate TLS PEM must be /etc/sister/gateway/tls.pem")
        require_private_file(pem, "GATEWAY_TLS_PEM", 0o640)
        if not CANDIDATE_ERROR_ROOT.is_dir():
            raise RenderError("candidate error root must be /etc/sister/gateway/errors")
        values["GATEWAY_ERROR_ROOT"] = str(CANDIDATE_ERROR_ROOT)
        values["GATEWAY_STATS_SOCKET"] = str(CANDIDATE_STATS_SOCKET)
    binary = require_absolute_safe_path(
        environment["GATEWAY_HAPROXY_BIN"],
        "GATEWAY_HAPROXY_BIN",
        must_exist=True,
        executable=True,
    )
    haproxy_version(binary)
    return values


def validate_governed_profile(profile_path):
    profile = load_json(profile_path)
    schema = load_json(ROOT / "contracts/gateway_security_profile.schema.json")
    errors = validate_profile(profile, schema)
    if errors:
        raise RenderError("gateway security profile is invalid: " + errors[0])
    if profile["status"] != "PROFILE_DEFINED":
        raise RenderError("gateway security profile must remain PROFILE_DEFINED")
    if profile["realizability"]["verification_gate"] != "ISO-01":
        raise RenderError("gateway security profile has not entered ISO-01")
    resolution = profile["realizability"].get("laboratory_resolution", {})
    if resolution.get("state") != "LAB_PROVEN_WITH_RESTRICTIONS":
        raise RenderError("gateway security profile lacks the SEC-03B-R decision")
    if profile["realizability"]["lua_allowed"] or profile["realizability"]["third_party_modules_allowed"]:
        raise RenderError("SEC-03B forbids Lua and third-party modules")
    return profile


def render(template, values):
    rendered = template
    for name, replacement in values.items():
        rendered = rendered.replace(f"@@{name}@@", replacement)
    remaining = PLACEHOLDER.findall(rendered)
    if remaining:
        raise RenderError("unresolved placeholders: " + ", ".join(sorted(set(remaining))))
    for forbidden in FORBIDDEN_CONFIG:
        if forbidden.search(rendered):
            raise RenderError("rendered configuration contains a forbidden dynamic or extension directive")
    expected_server = f"server sisterd unix@{values['GATEWAY_UPSTREAM_SOCKET']} check maxconn 32 maxqueue 64"
    if rendered.count(expected_server) != 1:
        raise RenderError("rendered configuration must contain exactly one fixed sisterd upstream")
    return rendered


def write_private_atomic(output, content, scope="lab", run_root=None):
    if scope in {"lab", "lan-lab"}:
        require_inside_run_root(output, "output", run_root)
    elif output != CANDIDATE_CONFIG:
        raise RenderError("candidate output must be /etc/sister/gateway/haproxy.cfg")
    if scope == "lab":
        output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(output.parent, 0o700)
    elif not output.parent.is_dir():
        raise RenderError("candidate configuration directory must already exist")
    descriptor, temporary_name = tempfile.mkstemp(prefix="haproxy.cfg.", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o640)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temporary, output)
        os.chmod(output, 0o640)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Render a governed SisTer HAProxy configuration")
    parser.add_argument("--profile", type=Path, default=PROFILE_PATH)
    parser.add_argument("--template", type=Path, default=TEMPLATE_PATH)
    parser.add_argument("--scope", choices=("lab", "lan-lab", "candidate"), default="lab")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    try:
        profile_path = require_absolute_safe_path(str(arguments.profile.resolve()), "profile", must_exist=True)
        template_path = require_absolute_safe_path(str(arguments.template.resolve()), "template", must_exist=True)
        default_output = DEFAULT_OUTPUT if arguments.scope in {"lab", "lan-lab"} else CANDIDATE_CONFIG
        output = require_absolute_safe_path(str((arguments.output or default_output).resolve()), "output")
        validate_governed_profile(profile_path)
        values = checked_environment(os.environ, arguments.scope)
        template = template_path.read_text(encoding="utf-8")
        rendered = render(template, values)
        write_private_atomic(output, rendered, arguments.scope, lab_run_root(os.environ))
    except (OSError, RenderError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"gateway configuration render failed: {exc}", file=sys.stderr)
        return 1
    print(f"gateway configuration rendered: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
