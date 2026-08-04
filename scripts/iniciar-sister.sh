#!/usr/bin/env bash

set -u

SERVICES=(
  "sisterd.service"
)

echo "=== Inicializacao do SisTer ==="
echo
echo "Somente o nucleo SisTer sera iniciado. Subsistemas reais nao pertencem ao ciclo operacional enquanto nao forem publicados por contratos assinados na Base Operacional."
echo

echo "[1/3] Recarregando configuracoes do systemd..."
systemctl --user daemon-reload

echo
echo "[2/3] Habilitando e iniciando servicos do nucleo..."

FAILED=()

for service in "${SERVICES[@]}"; do
    echo
    echo "-> Processando: $service"

    if systemctl --user enable --now "$service"; then
        echo "OK: $service habilitado e iniciado."
    else
        echo "Falha ao iniciar $service."
        FAILED+=("$service")
    fi
done

echo
echo "[3/3] Estado atual:"
echo

for service in "${SERVICES[@]}"; do
    active_status="$(systemctl --user is-active "$service" 2>/dev/null || true)"
    enabled_status="$(systemctl --user is-enabled "$service" 2>/dev/null || true)"

    printf "%-25s ativo: %-10s habilitado: %s\n" \
        "$service" "$active_status" "$enabled_status"
done

echo

if (( ${#FAILED[@]} > 0 )); then
    echo "Alguns servicos falharam:"
    printf '  - %s\n' "${FAILED[@]}"

    echo
    echo "Para consultar os logs:"
    for service in "${FAILED[@]}"; do
        echo "  journalctl --user -u $service -n 100 --no-pager"
    done

    exit 1
fi

echo "OK: nucleo SisTer ativo."
