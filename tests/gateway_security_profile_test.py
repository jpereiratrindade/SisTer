#!/usr/bin/env python3
import copy
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_gateway_security_profile import validate_profile  # noqa: E402


def mutate(document, path, replacement):
    changed = copy.deepcopy(document)
    current = changed
    components = path.split(".")
    for component in components[:-1]:
        current = current[component]
    current[components[-1]] = replacement
    return changed


def main():
    profile = json.loads((ROOT / "ops/gateway/security-profile.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "contracts/gateway_security_profile.schema.json").read_text(encoding="utf-8"))
    assert not validate_profile(profile, schema)

    unsafe_mutations = (
        ("technology.initial_validated_floor", "3.2.11"),
        ("technology.initial_validated_floor", "3.2.99"),
        ("deployment.identity_key_visible_to_gateway", True),
        ("network.upstream_host", "client-controlled.example"),
        ("network.upstream_dynamic_destination", True),
        ("tls.minimum_version", "TLSv1.2"),
        ("http.host_wildcards_allowed", True),
        ("http.missing_or_duplicate_host_action", "forward"),
        ("http.absolute_form_action", "forward"),
        ("http.websocket_enabled", True),
        ("http.maximum_body_bytes", 16777216),
        ("http.minimum_request_receive_rate_bytes_per_second", 0),
        ("http.timeouts_seconds.request_headers_absolute", 60),
        ("headers.client_supplied_request_id_trusted", True),
        ("gates.external_production_authorized", True),
        ("gates.write_capabilities_authorized", True),
        ("realizability.laboratory_resolution.merge_authorized", True),
        ("realizability.laboratory_resolution.external_exposure_authorized", True),
    )
    for path, replacement in unsafe_mutations:
        errors = validate_profile(mutate(profile, path, replacement), schema)
        assert errors, f"unsafe mutation was accepted: {path}={replacement!r}"

    missing_strip = copy.deepcopy(profile)
    missing_strip["headers"]["strip_exact"].remove("X-Request-ID")
    assert validate_profile(missing_strip, schema)

    missing_threat = copy.deepcopy(profile)
    missing_threat["threats"].pop()
    assert validate_profile(missing_threat, schema)

    implemented_without_evidence = copy.deepcopy(profile)
    implemented_without_evidence["threats"][0]["state"] = "CONTROLLED_BASELINE"
    assert validate_profile(implemented_without_evidence, schema)

    unknown_control = copy.deepcopy(profile)
    unknown_control["http"]["trust_everything"] = True
    assert validate_profile(unknown_control, schema)

    false_native_claim = copy.deepcopy(profile)
    false_native_claim["realizability"]["requirements"][5]["state"] = "NATIVE_DOCUMENTED"
    assert validate_profile(false_native_claim, schema)

    false_host_conformance = copy.deepcopy(profile)
    false_host_conformance["realizability"]["laboratory_resolution"]["host_exception"]["state"] = "PROVEN"
    assert validate_profile(false_host_conformance, schema)

    print("gateway_security_profile_tests ok")


if __name__ == "__main__":
    main()
