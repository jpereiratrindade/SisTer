#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MIGRATION="${1:-storage/migrations/001_init.sql}"
"$ROOT_DIR/scripts/db/migrate.sh" dev "$MIGRATION"
