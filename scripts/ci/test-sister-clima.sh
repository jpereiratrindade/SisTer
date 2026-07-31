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

if [ ! -d "tests" ]; then
    echo "Diretório de testes não encontrado."
    exit 1
fi

# Executar pytest ou unittest conforme disponível
if "$PYTHON" -m pytest --version >/dev/null 2>&1; then
    "$PYTHON" -m pytest tests/ -v
else
    echo "pytest não disponível, usando unittest..."
    "$PYTHON" -m unittest discover -s tests
fi
