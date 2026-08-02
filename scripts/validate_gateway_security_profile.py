#!/usr/bin/env python3
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "ops/gateway/security-profile.json"
SCHEMA = ROOT / "contracts/gateway_security_profile.schema.json"


def value(document, path, errors):
    current = document
    for component in path.split("."):
        if not isinstance(current, dict) or component not in current:
            errors.append(f"missing field: {path}")
            return None
        current = current[component]
    return current


def expect(document, path, expected, errors):
    actual = value(document, path, errors)
    if actual is not None and actual != expected:
        errors.append(f"{path} must be {expected!r}, got {actual!r}")


def expect_set(document, path, expected, errors):
    actual = value(document, path, errors)
    if actual is None:
        return
    if not isinstance(actual, list) or len(actual) != len(set(actual)) or set(actual) != set(expected):
        errors.append(f"{path} must contain exactly {sorted(expected)!r}")


def expect_keys(document, path, expected, errors):
    actual = document if not path else value(document, path, errors)
    if actual is None:
        return
    if not isinstance(actual, dict):
        errors.append(f"{path or 'profile'} must be an object")
        return
    if set(actual) != set(expected):
        errors.append(f"{path or 'profile'} fields must be exactly {sorted(expected)!r}")


def validate_profile(profile, schema):
    errors = []

    expected_objects = {
        "": {
            "contract_id", "contract_version", "status", "technology", "realizability", "deployment",
            "network", "tls", "http", "headers", "rate_limits", "observability",
            "resource_limits", "rollback", "gates", "threats",
        },
        "technology": {
            "product", "edition", "approved_branch", "initial_validated_floor", "patch_policy",
            "version_verified_on", "official_release_index", "lts_eol", "plugins",
        },
        "realizability": {
            "verification_gate", "policy", "lua_allowed", "third_party_modules_allowed",
            "requirements", "laboratory_resolution", "sec_03c_resolution", "iso_01_resolution",
        },
        "deployment": {
            "service_manager", "package_signature_required", "runtime_user", "config_owner",
            "config_mode", "private_key_max_mode", "sisterd_user",
            "identity_key_visible_to_gateway", "offline_config_validation_required",
        },
        "network": {
            "external_https_port", "external_http_port_action", "upstream_transport",
            "upstream_socket", "upstream_lab_socket_scope",
            "upstream_protocol", "upstream_dynamic_destination", "upstream_access_scope",
            "sisterd_inbound_tcp", "socket_activation_required", "legacy_proxy_enabled",
            "legacy_websocket_proxy_enabled",
        },
        "tls": {
            "required", "minimum_version", "maximum_version", "cipher_suites",
            "certificate_source", "exact_hostname_required", "sni_action", "expired_certificate_action",
            "renewal_requires_validation_and_reload", "hsts_enabled",
        },
        "http": {
            "downstream_protocols", "upstream_protocol", "allowed_methods", "host_allowlist_source",
            "host_allowlist_minimum_entries", "host_wildcards_allowed",
            "missing_or_duplicate_host_action", "absolute_form_action",
            "unexpected_host_port_action", "websocket_enabled", "upgrade_enabled",
            "maximum_request_target_bytes", "maximum_header_count", "maximum_header_bytes",
            "maximum_body_bytes", "authentication_maximum_body_bytes",
            "maximum_upstream_response_bytes", "minimum_request_receive_rate_bytes_per_second",
            "duplicate_content_length_action", "transfer_encoding_action",
            "content_length_and_transfer_encoding_action", "ambiguous_whitespace_action",
            "timeouts_seconds", "connections",
        },
        "http.timeouts_seconds": {
            "tls_handshake", "request_headers_absolute", "request_body_absolute_target",
            "request_body_inactivity", "client_idle",
            "http_keep_alive", "upstream_connect", "upstream_queue", "upstream_response",
        },
        "http.connections": {"global_maximum", "per_origin_maximum"},
        "headers": {
            "strip_exact", "strip_prefixes", "rebuild", "client_supplied_identity_trusted",
            "client_supplied_origin_trusted", "client_supplied_request_id_trusted",
        },
        "headers.rebuild": {
            "X-Forwarded-For", "X-Forwarded-Host", "X-Forwarded-Proto", "X-Request-ID", "Host",
        },
        "rate_limits": {
            "global", "per_origin", "per_origin_route", "login_per_origin",
            "internal_sisterd_limiter_retained", "rejection_status", "retry_after_required",
        },
        "rate_limits.global": {"requests", "window_seconds"},
        "rate_limits.per_origin": {"requests", "window_seconds"},
        "rate_limits.per_origin_route": {"requests", "window_seconds"},
        "rate_limits.login_per_origin": {"requests", "window_seconds"},
        "resource_limits": {
            "upstream_concurrent_maximum", "backend_queue_maximum", "stick_tables",
            "full_table_policy", "usage_metrics", "runtime_socket_mode",
        },
        "resource_limits.stick_tables": {
            "connection_by_origin", "global_rate", "origin_rate", "origin_route_rate", "login_rate",
        },
        "resource_limits.stick_tables.connection_by_origin": {"capacity", "expiration_seconds"},
        "resource_limits.stick_tables.global_rate": {"capacity", "expiration_seconds"},
        "resource_limits.stick_tables.origin_rate": {"capacity", "expiration_seconds"},
        "resource_limits.stick_tables.origin_route_rate": {"capacity", "expiration_seconds"},
        "resource_limits.stick_tables.login_rate": {"capacity", "expiration_seconds"},
        "observability": {
            "structured_logs_required", "request_id_format", "log_fields", "forbidden_log_fields",
            "block_metrics_required", "end_to_end_correlation_required",
        },
        "rollback": {
            "preserve_previous_package", "preserve_previous_config", "preserve_previous_certificate",
            "offline_validation_before_reload", "external_and_internal_health_required",
            "allowed_failure_mode", "forbidden_fallbacks",
        },
        "gates": {
            "current", "required_before_release", "external_production_authorized",
            "functional_scope_expansion_authorized", "write_capabilities_authorized",
            "websocket_authorized", "clima_integration_authorized", "sec_02r_required_before_write",
        },
    }
    for path, expected in expected_objects.items():
        expect_keys(profile, path, expected, errors)

    expect(schema, "$schema", "https://json-schema.org/draft/2020-12/schema", errors)
    expect(
        schema,
        "$id",
        "https://sister.local/contracts/gateway-security-profile/1.3.0",
        errors,
    )

    expect(profile, "contract_id", "sister.gateway-security-profile", errors)
    expect(profile, "contract_version", "1.3.0", errors)
    expect(profile, "status", "PROFILE_DEFINED", errors)
    expect(profile, "technology.product", "haproxy", errors)
    expect(profile, "technology.edition", "community", errors)
    expect(profile, "technology.approved_branch", "3.2", errors)
    expect(profile, "technology.patch_policy", "latest_maintained_patch_at_or_above_floor", errors)
    expect(profile, "technology.version_verified_on", "2026-08-01", errors)
    expect(profile, "technology.official_release_index", "https://www.haproxy.org/", errors)
    expect(profile, "technology.lts_eol", "2030-Q2", errors)
    expect(profile, "technology.plugins", [], errors)

    minimum_version = value(profile, "technology.initial_validated_floor", errors)
    match = re.fullmatch(r"3\.2\.(\d+)", minimum_version or "")
    if not match or int(match.group(1)) != 22:
        errors.append("technology.initial_validated_floor must match the currently verified HAProxy 3.2.22 release")

    expect(profile, "realizability.verification_gate", "ISO-01", errors)
    expect(profile, "realizability.policy", "native_simple_or_record_residual_risk", errors)
    expect(profile, "realizability.lua_allowed", False, errors)
    expect(profile, "realizability.third_party_modules_allowed", False, errors)
    required_realizability = {
        "tls_1_3": "PROVEN",
        "http_1_1_only": "PROVEN",
        "absolute_header_deadline": "NATIVE_DOCUMENTED",
        "header_limits": "PROVEN",
        "request_body_limit": "PROVEN",
        "minimum_receive_rate": "MECHANISM_UNPROVEN",
        "upstream_response_limit": "MECHANISM_UNPROVEN",
        "request_id_lower_hex_32": "PROVEN",
        "strip_x_sister_prefix": "PROVEN",
        "multidimensional_rate_limiting": "PROVEN",
        "absolute_body_deadline": "PARTIALLY_PROVEN",
        "bounded_concurrency_and_queue": "PROVEN",
        "sanitized_gateway_observability": "PROVEN",
        "canonical_host_authority": "PROVEN",
        "duplicate_identical_host": "ACCEPTED_LAB_DIVERGENCE",
        "duplicate_divergent_host": "PROVEN",
        "duplicate_content_length": "PROVEN_BY_SAFE_NORMALIZATION",
        "complete_websocket_upgrade": "PROVEN_BY_REJECTION",
        "isolated_upgrade_fields": "PROVEN_BY_STRIPPING",
        "full_nexo_composition": "DEFERRED_TO_SEC-03V",
        "local_upstream_isolation": "PARTIALLY_PROVEN",
    }
    requirements = value(profile, "realizability.requirements", errors)
    if isinstance(requirements, list):
        observed = {}
        for requirement in requirements:
            if not isinstance(requirement, dict) or set(requirement) != {"id", "mechanism", "state"}:
                errors.append("each realizability requirement must contain id, mechanism and state")
                continue
            requirement_id = requirement.get("id")
            if requirement_id in observed:
                errors.append(f"duplicate realizability requirement: {requirement_id}")
            observed[requirement_id] = requirement.get("state")
            if not isinstance(requirement.get("mechanism"), str) or not requirement["mechanism"].strip():
                errors.append(f"realizability requirement {requirement_id} needs a mechanism statement")
        if observed != required_realizability:
            errors.append("realizability states must preserve the approved SEC-03B-R resolution")
    else:
        errors.append("realizability.requirements must be a list")

    resolution = value(profile, "realizability.laboratory_resolution", errors)
    resolution_keys = {
        "decision_id", "state", "decided_on", "evidence", "authorizes_next_gate",
        "merge_authorized", "release_authorized", "external_exposure_authorized", "host_exception",
    }
    if isinstance(resolution, dict):
        if set(resolution) != resolution_keys:
            errors.append("laboratory resolution fields must preserve the SEC-03B-R decision")
        for field, expected in {
            "decision_id": "SEC-03B-R",
            "state": "LAB_PROVEN_WITH_RESTRICTIONS",
            "decided_on": "2026-08-01",
            "evidence": "docs/evidence/security/SEC-03B.md",
            "authorizes_next_gate": "SEC-03C",
            "merge_authorized": False,
            "release_authorized": False,
            "external_exposure_authorized": False,
        }.items():
            if resolution.get(field) != expected:
                errors.append(f"realizability.laboratory_resolution.{field} must be {expected!r}")
        exception = resolution.get("host_exception")
        exception_keys = {
            "state", "owner", "justification", "scope", "residual_risk", "review_gate",
            "reopen_conditions",
        }
        if not isinstance(exception, dict) or set(exception) != exception_keys:
            errors.append("host exception must contain owner, scope, risk and review conditions")
        else:
            if exception.get("state") != "ACCEPTED_LAB_DIVERGENCE":
                errors.append("identical duplicate Host must remain an accepted divergence, not proven")
            if exception.get("owner") != "gateway and transport maintainers":
                errors.append("Host divergence must retain its accountable owner")
            if exception.get("review_gate") != "SEC-03V":
                errors.append("Host divergence must be reviewed at SEC-03V")
            for field in ("justification", "residual_risk"):
                if not isinstance(exception.get(field), str) or not exception[field].strip():
                    errors.append(f"Host divergence requires {field}")
            for field in ("scope", "reopen_conditions"):
                entries = exception.get(field)
                if not isinstance(entries, list) or not entries or len(entries) != len(set(entries)):
                    errors.append(f"Host divergence requires unique non-empty {field}")
    else:
        errors.append("realizability.laboratory_resolution must be an object")

    sec_03c = value(profile, "realizability.sec_03c_resolution", errors)
    expected_sec_03c = {
        "state": "LAB_PROVEN_WITH_RESTRICTIONS",
        "decided_on": "2026-08-02",
        "evidence": "docs/evidence/security/SEC-03C.md",
        "next_gate": "ISO-01",
        "merge_authorized": False,
        "release_authorized": False,
        "external_exposure_authorized": False,
    }
    if sec_03c != expected_sec_03c:
        errors.append("realizability.sec_03c_resolution must preserve the restricted laboratory decision")

    iso_01 = value(profile, "realizability.iso_01_resolution", errors)
    expected_iso_01 = {
        "state": "LAB_PROVEN_WITH_RESTRICTIONS",
        "decided_on": "2026-08-02",
        "evidence": "docs/evidence/security/ISO-01.md",
        "next_gate": "SEC-03V",
        "merge_authorized": False,
        "release_authorized": False,
        "external_exposure_authorized": False,
    }
    if iso_01 != expected_iso_01:
        errors.append("realizability.iso_01_resolution must preserve the restricted laboratory decision")

    for path, expected in {
        "deployment.service_manager": "systemd",
        "deployment.package_signature_required": True,
        "deployment.runtime_user": "sister-gateway",
        "deployment.config_owner": "root:sister-gateway",
        "deployment.config_mode": "0640",
        "deployment.private_key_max_mode": "0640",
        "deployment.sisterd_user": "sister",
        "deployment.identity_key_visible_to_gateway": False,
        "deployment.offline_config_validation_required": True,
        "network.external_https_port": 443,
        "network.external_http_port_action": "closed",
        "network.upstream_transport": "unix",
        "network.upstream_socket": "/run/sister/sisterd.sock",
        "network.upstream_lab_socket_scope": "private_runtime_directory",
        "network.upstream_protocol": "HTTP/1.1",
        "network.upstream_dynamic_destination": False,
        "network.upstream_access_scope": "gateway_user_or_cgroup_only",
        "network.sisterd_inbound_tcp": False,
        "network.socket_activation_required": True,
        "network.legacy_proxy_enabled": False,
        "network.legacy_websocket_proxy_enabled": False,
        "tls.required": True,
        "tls.minimum_version": "TLSv1.3",
        "tls.maximum_version": "TLSv1.3",
        "tls.certificate_source": "approved_ca",
        "tls.exact_hostname_required": True,
        "tls.sni_action": "reject_unknown_or_missing",
        "tls.expired_certificate_action": "fail_closed",
        "tls.renewal_requires_validation_and_reload": True,
        "tls.hsts_enabled": False,
        "http.upstream_protocol": "HTTP/1.1",
        "http.host_allowlist_source": "deployment_inventory",
        "http.host_allowlist_minimum_entries": 1,
        "http.host_wildcards_allowed": False,
        "http.missing_or_duplicate_host_action": "reject_missing_or_divergent_accept_identical_under_exception",
        "http.absolute_form_action": "reject",
        "http.unexpected_host_port_action": "reject",
        "http.websocket_enabled": False,
        "http.upgrade_enabled": False,
        "http.maximum_request_target_bytes": 8192,
        "http.maximum_header_count": 64,
        "http.maximum_header_bytes": 16384,
        "http.maximum_body_bytes": 1048576,
        "http.authentication_maximum_body_bytes": 65536,
        "http.maximum_upstream_response_bytes": 16777216,
        "http.minimum_request_receive_rate_bytes_per_second": 1024,
        "http.duplicate_content_length_action": "normalize_identical_reject_invalid_or_divergent",
        "http.transfer_encoding_action": "reject",
        "http.content_length_and_transfer_encoding_action": "reject",
        "http.ambiguous_whitespace_action": "reject",
        "http.timeouts_seconds.tls_handshake": 5,
        "http.timeouts_seconds.request_headers_absolute": 5,
        "http.timeouts_seconds.request_body_absolute_target": 10,
        "http.timeouts_seconds.request_body_inactivity": 15,
        "http.timeouts_seconds.client_idle": 15,
        "http.timeouts_seconds.http_keep_alive": 2,
        "http.timeouts_seconds.upstream_connect": 2,
        "http.timeouts_seconds.upstream_queue": 2,
        "http.timeouts_seconds.upstream_response": 15,
        "http.connections.global_maximum": 1024,
        "http.connections.per_origin_maximum": 32,
        "headers.client_supplied_identity_trusted": False,
        "headers.client_supplied_origin_trusted": False,
        "headers.client_supplied_request_id_trusted": False,
        "rate_limits.internal_sisterd_limiter_retained": True,
        "rate_limits.rejection_status": 429,
        "rate_limits.retry_after_required": True,
        "resource_limits.upstream_concurrent_maximum": 32,
        "resource_limits.backend_queue_maximum": 64,
        "resource_limits.full_table_policy": "evict_oldest_entries",
        "resource_limits.usage_metrics": "private_runtime_socket",
        "resource_limits.runtime_socket_mode": "0600",
        "resource_limits.stick_tables.connection_by_origin.capacity": 128,
        "resource_limits.stick_tables.connection_by_origin.expiration_seconds": 30,
        "resource_limits.stick_tables.global_rate.capacity": 1,
        "resource_limits.stick_tables.global_rate.expiration_seconds": 10,
        "resource_limits.stick_tables.origin_rate.capacity": 128,
        "resource_limits.stick_tables.origin_rate.expiration_seconds": 60,
        "resource_limits.stick_tables.origin_route_rate.capacity": 512,
        "resource_limits.stick_tables.origin_route_rate.expiration_seconds": 60,
        "resource_limits.stick_tables.login_rate.capacity": 128,
        "resource_limits.stick_tables.login_rate.expiration_seconds": 60,
        "observability.structured_logs_required": True,
        "observability.request_id_format": "^[0-9a-f]{32}$",
        "observability.block_metrics_required": True,
        "observability.end_to_end_correlation_required": True,
        "rollback.preserve_previous_package": True,
        "rollback.preserve_previous_config": True,
        "rollback.preserve_previous_certificate": True,
        "rollback.offline_validation_before_reload": True,
        "rollback.external_and_internal_health_required": True,
        "rollback.allowed_failure_mode": "external_unavailable",
        "gates.current": "SEC-03V",
        "gates.external_production_authorized": False,
        "gates.functional_scope_expansion_authorized": False,
        "gates.write_capabilities_authorized": False,
        "gates.websocket_authorized": False,
        "gates.clima_integration_authorized": False,
        "gates.sec_02r_required_before_write": True,
    }.items():
        expect(profile, path, expected, errors)

    expect_set(
        profile,
        "tls.cipher_suites",
        {
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256",
        },
        errors,
    )
    expect_set(profile, "http.downstream_protocols", {"HTTP/1.1"}, errors)
    expect_set(
        profile,
        "http.allowed_methods",
        {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"},
        errors,
    )
    expect_set(
        profile,
        "headers.strip_exact",
        {"X-Forwarded-For", "X-Forwarded-Host", "X-Forwarded-Proto", "X-Request-ID", "Forwarded"},
        errors,
    )
    expect_set(profile, "headers.strip_prefixes", {"X-Sister-"}, errors)
    expect(
        profile,
        "headers.rebuild",
        {
            "X-Forwarded-For": "observed_source_address",
            "X-Forwarded-Host": "canonical_allowed_host",
            "X-Forwarded-Proto": "https",
            "X-Request-ID": "generated_lower_hex_32",
            "Host": "canonical_allowed_host",
        },
        errors,
    )

    for scope, requests, window in (
        ("global", 1000, 10),
        ("per_origin", 120, 60),
        ("per_origin_route", 60, 60),
        ("login_per_origin", 10, 60),
    ):
        expect(profile, f"rate_limits.{scope}.requests", requests, errors)
        expect(profile, f"rate_limits.{scope}.window_seconds", window, errors)

    required_forbidden_logs = {
        "authorization",
        "cookie",
        "set-cookie",
        "request_body",
        "query_string",
        "sister_assertion",
        "private_key",
        "x-sister-*",
    }
    forbidden_logs = value(profile, "observability.forbidden_log_fields", errors)
    if not isinstance(forbidden_logs, list) or not required_forbidden_logs.issubset(forbidden_logs):
        errors.append("observability.forbidden_log_fields does not protect every sensitive field")

    expect_set(
        profile,
        "rollback.forbidden_fallbacks",
        {"public_sisterd_bind", "direct_port_8000", "legacy_proxy", "weaken_tls", "enable_websocket"},
        errors,
    )
    expect_set(profile, "gates.required_before_release", {"SEC-03B", "SEC-03C", "SEC-03V"}, errors)

    required_threats = {
        "TH-HTTP-02",
        "TH-HTTP-03",
        "TH-HTTP-04",
        "TH-WS-01",
        "TH-PROXY-01",
        "TH-PROXY-02",
        "TH-CONF-01",
        "TH-AUD-01",
    }
    threats = value(profile, "threats", errors)
    if isinstance(threats, list):
        ids = [threat.get("id") for threat in threats if isinstance(threat, dict)]
        if len(ids) != len(set(ids)) or set(ids) != required_threats:
            errors.append("threats must map each SEC-03 threat exactly once")
        for threat in threats:
            if not isinstance(threat, dict):
                errors.append("each threat mapping must be an object")
                continue
            if set(threat) != {"id", "control", "test", "evidence", "residual_risk", "owner", "state"}:
                errors.append(f"threat {threat.get('id', '<unknown>')} has unexpected or missing fields")
            for field in ("control", "test", "residual_risk", "owner"):
                if not isinstance(threat.get(field), str) or not threat[field].strip():
                    errors.append(f"threat {threat.get('id', '<unknown>')} requires {field}")
            if threat.get("evidence") != "SEC-03V_PENDING" or threat.get("state") != "PROFILE_DEFINED":
                errors.append(f"threat {threat.get('id', '<unknown>')} cannot claim implementation evidence")

    return errors


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read valid JSON from {path}: {exc}") from exc


def main():
    profile_path = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else DEFAULT_PROFILE
    if len(sys.argv) > 2:
        print("usage: validate_gateway_security_profile.py [profile.json]")
        return 2
    try:
        profile = load_json(profile_path)
        schema = load_json(SCHEMA)
    except RuntimeError as exc:
        print(f"gateway security profile validation failed\n- {exc}")
        return 1

    errors = validate_profile(profile, schema)
    if errors:
        print("gateway security profile validation failed")
        for error in errors:
            print(f"- {error}")
        return 1
    print("gateway security profile validation ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
