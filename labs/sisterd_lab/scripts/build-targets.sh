#!/usr/bin/env bash
set -Eeuo pipefail

LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_ROOT="${LAB_ROOT}/build"

build_one() {
    local name="$1"
    local source="${LAB_ROOT}/target/${name}"
    local build="${BUILD_ROOT}/${name}"

    echo "[Build] ${name}"
    cmake -S "$source" -B "$build" \
        -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE:-RelWithDebInfo}" \
        -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

    cmake --build "$build" --parallel "${BUILD_JOBS:-$(nproc)}"
}

build_one sisterd
build_one sisterctl
