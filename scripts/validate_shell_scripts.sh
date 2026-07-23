#!/usr/bin/env bash
set -euo pipefail

while IFS= read -r script; do
  bash -n "$script"
done < <(find scripts -type f -name '*.sh' -print | sort)

echo "shell script validation ok"
