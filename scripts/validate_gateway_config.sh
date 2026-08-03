#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
run_root="${GATEWAY_RUN_ROOT:-${repo_root}/.run/gateway}"
config_path="${1:-${run_root}/haproxy.cfg}"
haproxy_binary="${GATEWAY_HAPROXY_BIN:-}"

case "$run_root" in
  "$repo_root"/.run/*) ;;
  *)
    echo "gateway config validation failed: GATEWAY_RUN_ROOT must stay inside .run" >&2
    exit 1
    ;;
esac
if [[ "${config_path}" != /* ]]; then
  echo "gateway config validation failed: configuration path must be absolute" >&2
  exit 1
fi
if [[ "${config_path}" != "${run_root}/"* ]] || [[ ! -f "${config_path}" ]]; then
  echo "gateway config validation failed: configuration must be a file under ${run_root}" >&2
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
