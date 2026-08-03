#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 || -z "$1" || -z "$2" ]]; then
  echo "Uso: $0 \"Nome do administrador\" email@exemplo.org" >&2
  exit 2
fi
if [[ ! "$2" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
  echo "E-mail inválido: $2" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run/gateway"
AUTH_FILE="$RUN_DIR/auth-users.tsv"

if [[ -f "$RUN_DIR/lan-sisterd.pid" || -f "$RUN_DIR/haproxy.pid" ]]; then
  echo "Pare o gateway LAN antes de criar a conta:" >&2
  echo "  ./scripts/stop_gateway_lan_lab.sh" >&2
  exit 1
fi

mkdir -p "$RUN_DIR"
chmod 700 "$RUN_DIR"
cmake -S "$ROOT_DIR" -B "$ROOT_DIR/build"
cmake --build "$ROOT_DIR/build" --target sisterctl --parallel

echo "A senha será solicitada duas vezes e não será gravada no shell history."
SISTER_AUTH_FILE="$AUTH_FILE" \
  "$ROOT_DIR/build/apps/sisterctl/sisterctl" \
  auth bootstrap-admin "$1" "$2"
chmod 600 "$AUTH_FILE"
echo "Administrador do gateway LAN criado: $2"
echo "Agora execute ./scripts/run_gateway_lan_lab.sh."
