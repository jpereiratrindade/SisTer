#!/usr/bin/env bash
set -euo pipefail

cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
python3 scripts/validate_tool_contracts.py
python3 scripts/validate_governance_repo.py
python3 scripts/validate_local_resources.py
./scripts/validate_shell_scripts.sh
