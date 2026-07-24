#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8000}"

home_html="$(curl -fsS "http://127.0.0.1:${PORT}/")"
grep -q "Transformar sinais dispersos em compreensão compartilhada" <<<"$home_html"
grep -q "sistemas inteligentes de" <<<"$home_html"
grep -q "Projeto Plataforma Colaborativa Sul da Embrapa" <<<"$home_html"
grep -q 'href="https://www.embrapa.br/"' <<<"$home_html"
grep -q 'Carta-anual-2024-2025.pdf#page=13' <<<"$home_html"
grep -q 'rel="noopener noreferrer"' <<<"$home_html"
if grep -Eq \
  "MorfoCampo|DroneOps|CampoNode|Sister-Clima|Sister-Studio|Radar-Sister" \
  <<<"$home_html"
then
  echo "Public home exposes a federated system name." >&2
  exit 1
fi
public_javascript="$(curl -fsS "http://127.0.0.1:${PORT}/public.js")"
if grep -Eq \
  "MorfoCampo|DroneOps|CampoNode|Sister-Clima|Sister-Studio|Radar-Sister" \
  <<<"$public_javascript"
then
  echo "Public JavaScript exposes a federated system name." >&2
  exit 1
fi
curl -fsS "http://127.0.0.1:${PORT}/login" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null

for protected_path in \
  systems \
  contracts \
  evidence \
  diagnostics \
  integrations/sister-clima \
  integrations/sister-studio
do
  status="$(
    curl -sS -o /dev/null -w '%{http_code}' \
      "http://127.0.0.1:${PORT}/api/${protected_path}"
  )"
  if [[ "$status" != "401" ]]; then
    echo "Expected /api/${protected_path} to require authentication; received ${status}." >&2
    exit 1
  fi
done

app_status="$(
  curl -sS -o /dev/null -w '%{http_code}' \
    "http://127.0.0.1:${PORT}/app.js"
)"
if [[ "$app_status" != "401" ]]; then
  echo "Expected /app.js to require authentication; received ${app_status}." >&2
  exit 1
fi

app_alias_status="$(
  curl --path-as-is -sS -o /dev/null -w '%{http_code}' \
    "http://127.0.0.1:${PORT}/./app.js"
)"
if [[ "$app_alias_status" != "401" ]]; then
  echo "Expected normalized /app.js path to require authentication; received ${app_alias_status}." >&2
  exit 1
fi

echo "sisterd public and authentication boundary smoke test ok on port ${PORT}"
