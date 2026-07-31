#!/usr/bin/env bash
set -Eeuo pipefail

# Este script é chamado pelo evaluator.py com cwd = component_root (Sister-Clima)

# Detectar o interpretador Python a usar: prioriza o venv do componente
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    echo "Nenhum interpretador Python encontrado."
    exit 1
fi

echo "Usando interpretador: $PYTHON"

# Encontrar o entrypoint real
ENTRYPOINT=""
for p in app.py streamlit_app.py main.py src/app.py; do
    if [ -f "$p" ]; then
        ENTRYPOINT="$p"
        break
    fi
done

if [ -z "$ENTRYPOINT" ]; then
    echo "Entrypoint não encontrado para teste de importação."
    exit 1
fi

# Converter path para module (ex: src/app.py -> src.app)
MODULE=$(echo "$ENTRYPOINT" | sed 's/\.py$//' | tr '/' '.')

echo "Verificando sanidade de importação para $MODULE..."
"$PYTHON" -c "import sys; sys.path.insert(0, '.'); import $MODULE; print('Import OK')"
