#!/usr/bin/env bash
set -Eeuo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ROOT="${LAB_ROOT}/target"
MANIFEST_DIR="${LAB_ROOT}/manifests"

verify_manifest() {
    local tree="$1"
    local manifest="$2"
    local label="$3"

    [[ -d "$tree" ]] || {
        echo "[ERRO] Árvore ausente: $tree" >&2
        return 1
    }

    [[ -f "$manifest" ]] || {
        echo "[ERRO] Manifesto ausente: $manifest" >&2
        return 1
    }

    echo "[Verificação] $label"
    (
        cd "$tree"
        sha256sum --check --strict "$manifest"
    )
}

verify_manifest \
    "${TARGET_ROOT}/sisterd" \
    "${MANIFEST_DIR}/sisterd.sha256" \
    "snapshot do sisterd"

verify_manifest \
    "${TARGET_ROOT}/sisterctl" \
    "${MANIFEST_DIR}/sisterctl.sha256" \
    "snapshot do sisterctl"

echo "[OK] O snapshot permanece idêntico aos manifestos registrados."
