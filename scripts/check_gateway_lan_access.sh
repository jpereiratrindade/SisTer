#!/usr/bin/env bash
set -euo pipefail

GATEWAY_ADDRESS="${1:-${GATEWAY_LAN_ADDRESS:-}}"
CA_FILE="${2:-${GATEWAY_LAN_CA_FILE:-}}"
GATEWAY_HOST="${GATEWAY_ALLOWED_HOST:-sister-gateway.test}"
GATEWAY_PORT=8443

fail() {
  echo "ERRO: $1" >&2
  exit 1
}

[[ "$GATEWAY_ADDRESS" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || \
  fail "informe o IP do laptop: $0 10.163.80.176 /caminho/ca-lab.crt"
[[ -f "$CA_FILE" ]] || fail "CA não encontrada: $CA_FILE"

echo "1/4 Nome local"
if getent hosts "$GATEWAY_HOST" | awk '{print $1}' | grep -Fxq "$GATEWAY_ADDRESS"; then
  echo "OK: $GATEWAY_HOST -> $GATEWAY_ADDRESS"
else
  echo "FALHA: $GATEWAY_HOST não aponta para $GATEWAY_ADDRESS"
  echo "Adicione esta linha em /etc/hosts neste computador:"
  echo "$GATEWAY_ADDRESS $GATEWAY_HOST"
  exit 2
fi

echo "2/4 Porta TCP"
if timeout 3 bash -c "</dev/tcp/$GATEWAY_ADDRESS/$GATEWAY_PORT" 2>/dev/null; then
  echo "OK: $GATEWAY_ADDRESS:$GATEWAY_PORT aceita conexão"
else
  echo "FALHA: não foi possível conectar em $GATEWAY_ADDRESS:$GATEWAY_PORT"
  echo "Verifique se o gateway está rodando e se o firewall do laptop permite TCP 8443."
  exit 3
fi

echo "3/4 Certificado TLS"
if curl --noproxy '*' --silent --show-error --fail \
    --connect-timeout 3 --max-time 6 \
    --resolve "$GATEWAY_HOST:$GATEWAY_PORT:$GATEWAY_ADDRESS" \
    --cacert "$CA_FILE" \
    "https://$GATEWAY_HOST:$GATEWAY_PORT/api/health" >/tmp/sister-gateway-health.json; then
  echo "OK: certificado confiável e SNI/Host aceitos"
else
  echo "FALHA: TLS ou certificado não foi aceito"
  echo "A CA correta é a que foi gerada na mesma execução do gateway: $CA_FILE"
  exit 4
fi

echo "4/4 Aplicação"
cat /tmp/sister-gateway-health.json
echo
echo "OK: acesso ao SisTer funcionando"
