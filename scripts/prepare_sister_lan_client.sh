#!/usr/bin/env bash
# SISTER-INFRA-LEGACY-GATEWAY
# Legado de transição: a execução operacional de gateway/TLS/LAN do ecossistema
# pertence ao repositório Sister-Infra. Este script permanece temporariamente
# para reprodução de baselines e testes históricos; não ampliar sua responsabilidade.
set -Eeuo pipefail

GATEWAY_IP="${1:-}"
GATEWAY_HOST="${2:-sister-gateway.test}"
CA_SOURCE="${3:-}"

usage() {
  cat <<'EOF'
Uso:
  sudo ./prepare_sister_lan_client.sh <IP_GATEWAY> [HOSTNAME] <CAMINHO_CA>

Exemplo:
  sudo ./prepare_sister_lan_client.sh \
    10.163.80.176 \
    sister-gateway.test \
    /tmp/sister-ca-lab.crt
EOF
}

fail() {
  printf 'ERRO: %s\n' "$*" >&2
  exit 1
}

[[ -n "$GATEWAY_IP" ]] || { usage; exit 2; }
[[ -n "$CA_SOURCE" ]] || { usage; exit 2; }
[[ $EUID -eq 0 ]] || fail "execute com sudo."
[[ -f "$CA_SOURCE" ]] || fail "certificado CA não encontrado: $CA_SOURCE"

if ! [[ "$GATEWAY_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  fail "IPv4 inválido: $GATEWAY_IP"
fi

HOSTS_FILE="/etc/hosts"
TMP_HOSTS="$(mktemp)"
trap 'rm -f "$TMP_HOSTS"' EXIT

# Remove entradas antigas do mesmo hostname e grava uma única entrada atual.
awk -v host="$GATEWAY_HOST" '
{
  keep=1
  for (i=2; i<=NF; i++) {
    if ($i == host) keep=0
  }
  if (keep) print
}
' "$HOSTS_FILE" > "$TMP_HOSTS"

printf '%s %s\n' "$GATEWAY_IP" "$GATEWAY_HOST" >> "$TMP_HOSTS"
install -m 0644 "$TMP_HOSTS" "$HOSTS_FILE"

install_ca_fedora() {
  local dst="/etc/pki/ca-trust/source/anchors/sister-gateway-lab-ca.crt"
  install -m 0644 "$CA_SOURCE" "$dst"
  update-ca-trust
  printf 'CA instalada em: %s\n' "$dst"
}

install_ca_debian() {
  local dst="/usr/local/share/ca-certificates/sister-gateway-lab-ca.crt"
  install -m 0644 "$CA_SOURCE" "$dst"
  update-ca-certificates
  printf 'CA instalada em: %s\n' "$dst"
}

if command -v update-ca-trust >/dev/null 2>&1; then
  install_ca_fedora
elif command -v update-ca-certificates >/dev/null 2>&1; then
  install_ca_debian
else
  fail "sistema sem update-ca-trust ou update-ca-certificates."
fi

printf '\nPreparação concluída.\n'
printf 'Host: %s -> %s\n' "$GATEWAY_HOST" "$GATEWAY_IP"
printf 'URL:  https://%s:8443\n' "$GATEWAY_HOST"

if command -v curl >/dev/null 2>&1; then
  printf '\nTeste HTTPS:\n'
  curl --noproxy '*' \
    --fail \
    --silent \
    --show-error \
    --connect-timeout 5 \
    "https://${GATEWAY_HOST}:8443/" >/dev/null \
    && printf '[PASS] Gateway acessível e certificado confiável.\n' \
    || printf '[WARN] Preparação concluída, mas o teste HTTPS falhou.\n'
fi
