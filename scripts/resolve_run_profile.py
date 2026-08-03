#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "config" / "run_profiles.json"
PROFILE_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
PROJECT_ID = re.compile(r"[a-z0-9][a-z0-9_]*")


def load_profiles():
    document = json.loads(PROFILES.read_text(encoding="utf-8"))
    if document.get("version") != "1.0.0" or set(document) != {"version", "profiles"}:
        raise ValueError("run profile contract must be version 1.0.0")
    profiles = document.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("run profile contract must contain profiles")
    registry = json.loads((ROOT / "config" / "local_resources.json").read_text(encoding="utf-8"))
    governed = {
        project["id"]
        for project in registry["projects"]
        if project.get("orchestration", {}).get("policy") == "ensure-running"
    }
    for name, profile in profiles.items():
        if not PROFILE_NAME.fullmatch(name) or not isinstance(profile, dict):
            raise ValueError(f"invalid run profile: {name}")
        required_fields = {
            "environment", "default_port", "scope", "gateway_dynamic_tests",
            "access_scope", "core_transport", "public_gateway", "subsystems",
            "gate_closure_authorized",
        }
        if set(profile) != required_fields:
            raise ValueError(f"invalid fields in run profile: {name}")
        if profile["environment"] not in {"dev", "test"}:
            raise ValueError(f"invalid environment in run profile: {name}")
        if not isinstance(profile["default_port"], int) or not 1 <= profile["default_port"] <= 65535:
            raise ValueError(f"invalid port in run profile: {name}")
        if profile["scope"] not in {"core", "ecosystem", "sec-03v-prerequisites"}:
            raise ValueError(f"invalid scope in run profile: {name}")
        if profile["access_scope"] not in {
            "LOCAL_ONLY", "LOCAL_TEST", "LAN_FEDERATED", "SECURITY_VALIDATION"
        }:
            raise ValueError(f"invalid access scope in run profile: {name}")
        if profile["core_transport"] not in {"loopback-tcp", "unix-socket"}:
            raise ValueError(f"invalid core transport in run profile: {name}")
        if profile["public_gateway"] not in {
            "not-requested", "lan-required", "validation-only"
        }:
            raise ValueError(f"invalid public gateway in run profile: {name}")
        if profile["access_scope"] == "LAN_FEDERATED" and (
            profile["core_transport"] != "unix-socket"
            or profile["public_gateway"] != "lan-required"
        ):
            raise ValueError(f"LAN profile must use the federated Unix gateway: {name}")
        if profile["access_scope"] in {"LOCAL_ONLY", "LOCAL_TEST"} and (
            profile["core_transport"] != "loopback-tcp"
            or profile["public_gateway"] != "not-requested"
        ):
            raise ValueError(f"local profile cannot publish a gateway: {name}")
        if profile["gateway_dynamic_tests"] not in {"optional", "required"}:
            raise ValueError(f"invalid gateway policy in run profile: {name}")
        if profile["gate_closure_authorized"] is not False:
            raise ValueError(f"run profile cannot authorize gate closure: {name}")
        subsystems = profile["subsystems"]
        if not isinstance(subsystems, dict) or set(subsystems) != {
            "selection", "projects", "required", "failure_policy"
        }:
            raise ValueError(f"invalid subsystem policy in run profile: {name}")
        selection = subsystems["selection"]
        projects = subsystems["projects"]
        required = subsystems["required"]
        failure_policy = subsystems["failure_policy"]
        if selection not in {"none", "all", "listed"}:
            raise ValueError(f"invalid subsystem selection in run profile: {name}")
        if failure_policy not in {"warn", "block"}:
            raise ValueError(f"invalid subsystem failure policy in run profile: {name}")
        if not all(
            isinstance(values, list)
            and len(values) == len(set(values))
            and all(isinstance(value, str) and PROJECT_ID.fullmatch(value) for value in values)
            for values in (projects, required)
        ):
            raise ValueError(f"invalid subsystem ids in run profile: {name}")
        if selection == "listed" and not projects:
            raise ValueError(f"listed run profile has no projects: {name}")
        if selection != "listed" and projects:
            raise ValueError(f"unexpected project list in run profile: {name}")
        if not set(required).issubset(projects if selection == "listed" else set()):
            raise ValueError(f"required subsystem is not selected in run profile: {name}")
        if not set(projects).issubset(governed):
            raise ValueError(f"unknown governed subsystem in run profile: {name}")
        if profile["scope"] == "sec-03v-prerequisites" and (
            profile["gateway_dynamic_tests"] != "required"
            or required != ["sister_reference"]
            or failure_policy != "block"
        ):
            raise ValueError("SEC-03V prerequisites must require HAProxy and sister_reference")
    return profiles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    profiles = load_profiles()
    if args.check:
        print(f"run profile validation ok: {len(profiles)} profiles")
        return 0
    if not args.profile or args.profile not in profiles:
        raise ValueError(f"unknown run profile: {args.profile or '<missing>'}")
    profile = profiles[args.profile]
    subsystems = profile["subsystems"]
    values = [
        profile["environment"],
        str(profile["default_port"]),
        profile["scope"],
        profile["access_scope"],
        profile["core_transport"],
        profile["public_gateway"],
        profile["gateway_dynamic_tests"],
        subsystems["selection"],
        ",".join(subsystems["projects"]) or "-",
        ",".join(subsystems["required"]) or "-",
        subsystems["failure_policy"],
    ]
    print("\n".join(values))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"run profile error: {error}", file=sys.stderr)
        sys.exit(3)
