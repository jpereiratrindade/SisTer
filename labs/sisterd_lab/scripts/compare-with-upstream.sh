#!/usr/bin/env bash
set -Eeuo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "${LAB_ROOT}/manifests/snapshot.env"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

copy_normalized() {
    local source="$1"
    local destination="$2"

    mkdir -p "$destination"
    rsync -a --delete \
        --exclude='.git/' \
        --exclude='CMakeFiles/' \
        --exclude='CMakeCache.txt' \
        --exclude='cmake_install.cmake' \
        --exclude='CTestTestfile.cmake' \
        --exclude='compile_commands.json' \
        --exclude='Makefile' \
        --exclude='*.o' \
        --exclude='*.obj' \
        --exclude='*.a' \
        --exclude='*.so' \
        --exclude='*.so.*' \
        --exclude='*.out' \
        --exclude='*.gcda' \
        --exclude='*.gcno' \
        --exclude='*.profraw' \
        --exclude='*.profdata' \
        --exclude='build/' \
        --exclude='_build/' \
        "$source/" "$destination/"
}

compare_tree() {
    local upstream="$1"
    local snapshot="$2"
    local label="$3"
    local normalized="${TMP_DIR}/${label}"

    [[ -d "$upstream" ]] || {
        echo "[ERRO] Origem indisponível: $upstream" >&2
        return 1
    }

    copy_normalized "$upstream" "$normalized"

    if diff -ruN -- "$normalized" "$snapshot"; then
        echo "[OK] $label é ipsis litteris em relação à origem normalizada."
    else
        echo "[DIVERGÊNCIA] $label difere da origem." >&2
        return 1
    fi
}

compare_tree "$SOURCE_SISTERD" "${LAB_ROOT}/target/sisterd" "sisterd"
compare_tree "$SOURCE_SISTERCTL" "${LAB_ROOT}/target/sisterctl" "sisterctl"
