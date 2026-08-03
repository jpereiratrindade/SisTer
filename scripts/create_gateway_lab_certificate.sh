#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${GATEWAY_RUN_ROOT:-$ROOT_DIR/.run/gateway}"
LAB_HOST="${1:-${GATEWAY_ALLOWED_HOST:-sister-gateway.test}}"

case "$RUN_DIR" in
  "$ROOT_DIR"/.run/*) ;;
  *)
    echo "gateway certificate creation failed: GATEWAY_RUN_ROOT must stay inside $ROOT_DIR/.run" >&2
    exit 1
    ;;
esac

if [[ ! "$LAB_HOST" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$ ]] ||
   [[ "$LAB_HOST" == *"*"* ]] || [[ "$LAB_HOST" != *.test ]]; then
  echo "gateway certificate creation failed: host must be one exact DNS name under .test" >&2
  exit 1
fi
if ! command -v openssl >/dev/null 2>&1; then
  echo "gateway certificate creation failed: openssl is required" >&2
  exit 1
fi

mkdir -p "$RUN_DIR"
chmod 700 "$RUN_DIR"
umask 077

CA_KEY="$RUN_DIR/ca-lab.key"
CA_CERT="$RUN_DIR/ca-lab.crt"
SERVER_KEY="$RUN_DIR/gateway-lab.key"
SERVER_CSR="$RUN_DIR/gateway-lab.csr"
SERVER_CERT="$RUN_DIR/gateway-lab.crt"
COMBINED_PEM="$RUN_DIR/gateway-lab.pem"
EXT_FILE="$RUN_DIR/gateway-lab.ext"

openssl req -x509 -newkey rsa:3072 -sha256 -nodes -days 7 \
  -subj "/CN=SisTer SEC-03B Lab CA" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -addext "subjectKeyIdentifier=hash" \
  -keyout "$CA_KEY" -out "$CA_CERT" >/dev/null 2>&1
openssl req -new -newkey rsa:3072 -sha256 -nodes \
  -subj "/CN=$LAB_HOST" \
  -keyout "$SERVER_KEY" -out "$SERVER_CSR" >/dev/null 2>&1

printf 'subjectAltName=DNS:%s\nextendedKeyUsage=serverAuth\nkeyUsage=digitalSignature,keyEncipherment\n' \
  "$LAB_HOST" >"$EXT_FILE"
openssl x509 -req -sha256 -days 7 -in "$SERVER_CSR" \
  -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial \
  -extfile "$EXT_FILE" -out "$SERVER_CERT" >/dev/null 2>&1

cp "$SERVER_CERT" "$COMBINED_PEM"
printf '\n' >>"$COMBINED_PEM"
sed -n '/-----BEGIN PRIVATE KEY-----/,/-----END PRIVATE KEY-----/p' \
  "$SERVER_KEY" >>"$COMBINED_PEM"
chmod 600 "$CA_KEY" "$SERVER_KEY" "$COMBINED_PEM"
chmod 644 "$CA_CERT" "$SERVER_CERT"
rm -f "$SERVER_CSR" "$EXT_FILE" "$RUN_DIR/ca-lab.srl"

openssl verify -CAfile "$CA_CERT" "$SERVER_CERT" >/dev/null
openssl x509 -in "$SERVER_CERT" -noout -checkhost "$LAB_HOST" >/dev/null
echo "gateway lab certificate created for $LAB_HOST in $RUN_DIR"
