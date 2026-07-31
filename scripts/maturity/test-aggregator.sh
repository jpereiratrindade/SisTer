#!/usr/bin/env bash
set -Eeuo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME_ROOT="$REPO/.run/maturity"
COMPONENTS_DIR="$RUNTIME_ROOT/components"
INDEX_FILE="$RUNTIME_ROOT/components.json"

echo "=== Testando Agregador de Maturidade ==="

# 1. Executa agregador puro
python3 "$REPO/scripts/maturity/aggregate-components.py"

if [[ ! -f "$INDEX_FILE" ]]; then
    echo "FALHA: components.json não foi criado"
    exit 1
fi

SCHEMA=$(grep -o '"schema": "[^"]*"' "$INDEX_FILE" | cut -d'"' -f4)
if [[ "$SCHEMA" != "sister.maturity-components/1.0.0" ]]; then
    echo "FALHA: Schema incorreto: $SCHEMA"
    exit 1
fi

MISSING=$(grep -c '"profile_state": "missing"' "$INDEX_FILE" || true)
if [[ "$MISSING" -eq 0 ]]; then
    echo "FALHA: Não identificou componentes sem perfil"
    exit 1
fi

echo "SUCESSO: Agregador funcionou corretamente"
