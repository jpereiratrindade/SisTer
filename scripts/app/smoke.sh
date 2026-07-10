#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8000}"

curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/api/systems" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/api/contracts" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/api/evidence" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/api/diagnostics" >/dev/null

echo "sisterd smoke test ok on port ${PORT}"
