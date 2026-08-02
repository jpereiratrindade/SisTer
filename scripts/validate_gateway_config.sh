#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
config_path="${1:-${repo_root}/.run/gateway/haproxy.cfg}"
haproxy_binary="${GATEWAY_HAPROXY_BIN:-}"

if [[ "${config_path}" != /* ]]; then
  echo "gateway config validation failed: configuration path must be absolute" >&2
  exit 1
fi
if [[ "${config_path}" != "${repo_root}/.run/gateway/"* ]] || [[ ! -f "${config_path}" ]]; then
  echo "gateway config validation failed: configuration must be a file under .run/gateway" >&2
  exit 1
fi
if [[ -z "${haproxy_binary}" || "${haproxy_binary}" != /* || ! -x "${haproxy_binary}" ]]; then
  echo "gateway config validation failed: GATEWAY_HAPROXY_BIN must be an absolute executable" >&2
  exit 1
fi

python3 "${repo_root}/scripts/validate_gateway_security_profile.py"
haproxy_version_output="$("${haproxy_binary}" -vv)"
grep -Eq '^HAProxy version 3\.2\.(2[2-9]|[3-9][0-9]|[1-9][0-9]{2,})([^0-9]|$)' \
  <<<"${haproxy_version_output}"
"${haproxy_binary}" -c -V -f "${config_path}"

echo "gateway configuration validation ok"
