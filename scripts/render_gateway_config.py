#!/usr/bin/env python3
import argparse
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


def require_inside_run_root(path, name):
    resolved_parent = path.parent.resolve()
    run_root = RUN_ROOT.resolve()
    if resolved_parent != run_root and run_root not in resolved_parent.parents:
        raise RenderError(f"{name} must remain inside {run_root}")


def require_private_file(path, name):
    if path.is_symlink() or not path.is_file():
        raise RenderError(f"{name} must be a regular non-symlink file")
    permissions = stat.S_IMODE(path.stat().st_mode)
    if permissions & 0o077:
        raise RenderError(f"{name} permissions must be 0600 or stricter")


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


def checked_environment(environment):
    required = {
        "GATEWAY_TLS_PEM",
        "GATEWAY_ALLOWED_HOST",
        "GATEWAY_CANONICAL_HOST",
        "GATEWAY_HAPROXY_BIN",
    }
    missing = sorted(name for name in required if not environment.get(name))
    if missing:
        raise RenderError("missing environment: " + ", ".join(missing))

    values = {
        "GATEWAY_TLS_PEM": environment["GATEWAY_TLS_PEM"],
        "GATEWAY_ALLOWED_HOST": environment["GATEWAY_ALLOWED_HOST"].lower(),
        "GATEWAY_CANONICAL_HOST": environment["GATEWAY_CANONICAL_HOST"].lower(),
        "GATEWAY_LISTEN_ADDRESS": environment.get("GATEWAY_LISTEN_ADDRESS", "127.0.0.1"),
        "GATEWAY_LISTEN_PORT": environment.get("GATEWAY_LISTEN_PORT", "8443"),
        "GATEWAY_UPSTREAM_ADDRESS": environment.get("GATEWAY_UPSTREAM_ADDRESS", "127.0.0.1"),
        "GATEWAY_UPSTREAM_PORT": environment.get("GATEWAY_UPSTREAM_PORT", "8000"),
        "GATEWAY_ERROR_ROOT": str((ROOT / "ops/gateway/haproxy/errors").resolve()),
        "GATEWAY_STATS_SOCKET": str((RUN_ROOT / "haproxy.sock").resolve()),
    }
    if values["GATEWAY_LISTEN_ADDRESS"] != "127.0.0.1":
        raise RenderError("laboratory listener must be 127.0.0.1")
    if values["GATEWAY_LISTEN_PORT"] != "8443":
        raise RenderError("laboratory listener port must be 8443")
    if values["GATEWAY_UPSTREAM_ADDRESS"] != "127.0.0.1" or values["GATEWAY_UPSTREAM_PORT"] != "8000":
        raise RenderError("laboratory upstream must be 127.0.0.1:8000")
    allowed_host = values["GATEWAY_ALLOWED_HOST"]
    if not HOST.fullmatch(allowed_host) or "*" in allowed_host or not allowed_host.endswith(".test"):
        raise RenderError("laboratory Host must be one exact DNS name under .test")
    if values["GATEWAY_CANONICAL_HOST"] != allowed_host:
        raise RenderError("canonical and allowed laboratory Host must match")

    pem = require_absolute_safe_path(values["GATEWAY_TLS_PEM"], "GATEWAY_TLS_PEM", must_exist=True)
    require_inside_run_root(pem, "GATEWAY_TLS_PEM")
    require_private_file(pem, "GATEWAY_TLS_PEM")
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
    if profile["realizability"]["verification_gate"] != "SEC-03C":
        raise RenderError("gateway security profile has not closed SEC-03B")
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
    expected_server = f"server sisterd {values['GATEWAY_UPSTREAM_ADDRESS']}:{values['GATEWAY_UPSTREAM_PORT']} check maxconn 32 maxqueue 64"
    if rendered.count(expected_server) != 1:
        raise RenderError("rendered configuration must contain exactly one fixed sisterd upstream")
    return rendered


def write_private_atomic(output, content):
    require_inside_run_root(output, "output")
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(output.parent, 0o700)
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
    parser = argparse.ArgumentParser(description="Render the governed SEC-03B/03C HAProxy lab configuration")
    parser.add_argument("--profile", type=Path, default=PROFILE_PATH)
    parser.add_argument("--template", type=Path, default=TEMPLATE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    try:
        profile_path = require_absolute_safe_path(str(arguments.profile.resolve()), "profile", must_exist=True)
        template_path = require_absolute_safe_path(str(arguments.template.resolve()), "template", must_exist=True)
        output = require_absolute_safe_path(str(arguments.output.resolve()), "output")
        validate_governed_profile(profile_path)
        values = checked_environment(os.environ)
        template = template_path.read_text(encoding="utf-8")
        rendered = render(template, values)
        write_private_atomic(output, rendered)
    except (OSError, RenderError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"gateway configuration render failed: {exc}", file=sys.stderr)
        return 1
    print(f"gateway configuration rendered: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
