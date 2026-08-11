#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 || -z "$1" || -z "$2" ]]; then
  echo "Uso: $0 \"Nome do administrador\" email@exemplo.org" >&2
  exit 2
fi

NAME="$1"
EMAIL="$2"
ENVIRONMENT="dev"

if [[ ! "$EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
  echo "E-mail inválido: $EMAIL" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run/gateway"
cd "$ROOT_DIR"

if [[ -f "$RUN_DIR/lan-sisterd.pid" || -f "$RUN_DIR/haproxy.pid" ]]; then
  echo "Pare o gateway LAN antes de criar a conta:" >&2
  echo "  ./scripts/stop_gateway_lan_lab.sh" >&2
  exit 1
fi

echo "=== Bootstrap administrativo do SisTer ==="
echo
echo "Ambiente: $ENVIRONMENT"
echo "Autoridade persistente: PostgreSQL / sister_users"
echo "Backend de autenticação: PostgreSQL"
echo

scripts/db/up.sh "$ENVIRONMENT"
scripts/db/migrate.sh "$ENVIRONMENT"

existing_admin="$(
  scripts/auth/userctl.sh --environment "$ENVIRONMENT" list |
    awk -F '|' '
      function trim(value) {
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
        return value
      }
      NR > 2 && trim($4) == "admin" && trim($5) == "t" {
        print trim($2)
        exit
      }
    '
)"

if [[ -n "$existing_admin" ]]; then
  echo "Já existe administrador ativo no SisTer: $existing_admin" >&2
  echo "Use scripts/auth/userctl.sh para administrar contas persistentes." >&2
  exit 1
fi

echo "A senha será solicitada duas vezes e não será gravada no shell history."
echo

scripts/auth/userctl.sh \
  --environment "$ENVIRONMENT" \
  create "$EMAIL" "$NAME" admin


echo
echo "Administrador persistente criado: $EMAIL"
echo "A identidade foi gravada em sister_users."
echo "O perfil dev-lan autenticará diretamente no PostgreSQL."
echo "Agora inicie o perfil dev-lan."
