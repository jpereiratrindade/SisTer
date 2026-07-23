#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8000}"

curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/login" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/api/systems" >/dev/null

for protected_path in contracts evidence diagnostics; do
  status="$(
    curl -sS -o /dev/null -w '%{http_code}' \
      "http://127.0.0.1:${PORT}/api/${protected_path}"
  )"
  if [[ "$status" != "401" ]]; then
    echo "Expected /api/${protected_path} to require authentication; received ${status}." >&2
    exit 1
  fi
done

echo "sisterd public and authentication boundary smoke test ok on port ${PORT}"
