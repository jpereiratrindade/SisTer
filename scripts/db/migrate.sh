#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-dev}"
REQUESTED_MIGRATION="${2:-}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$ROOT_DIR"

# shellcheck source=../lib/sister_env.sh
source scripts/lib/sister_env.sh
sister_load_env "$ENV_NAME"

db_query() {
  local sql="${1:?sql required}"

  if command -v psql >/dev/null 2>&1; then
    psql "$SISTER_DATABASE_URL" \
      -X -A -t -v ON_ERROR_STOP=1 \
      -c "$sql"
  elif command -v docker >/dev/null 2>&1 &&
       docker ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
    printf '%s\n' "$sql" |
      docker exec -i "$SISTER_DB_CONTAINER" sh -lc \
        'psql -X -A -t -v ON_ERROR_STOP=1 \
          -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
  elif command -v podman >/dev/null 2>&1 &&
       podman ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
    printf '%s\n' "$sql" |
      podman exec -i "$SISTER_DB_CONTAINER" sh -lc \
        'psql -X -A -t -v ON_ERROR_STOP=1 \
          -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
  else
    echo "No psql client found and no running ${SISTER_DB_CONTAINER} container found." >&2
    echo "Run ./scripts/db/up.sh ${SISTER_ENV} first, or install psql." >&2
    return 1
  fi
}

db_apply_file() {
  local migration="${1:?migration required}"

  if command -v psql >/dev/null 2>&1; then
    psql "$SISTER_DATABASE_URL" \
      -X -v ON_ERROR_STOP=1 \
      -f "$migration"
  elif command -v docker >/dev/null 2>&1 &&
       docker ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
    docker exec -i "$SISTER_DB_CONTAINER" sh -lc \
      'psql -X -v ON_ERROR_STOP=1 \
        -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
      < "$migration"
  elif command -v podman >/dev/null 2>&1 &&
       podman ps --format '{{.Names}}' | grep -qx "$SISTER_DB_CONTAINER"; then
    podman exec -i "$SISTER_DB_CONTAINER" sh -lc \
      'psql -X -v ON_ERROR_STOP=1 \
        -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
      < "$migration"
  else
    echo "No psql client found and no running ${SISTER_DB_CONTAINER} container found." >&2
    return 1
  fi
}

migration_table_exists() {
  [[ "$(db_query "
    SELECT count(*)
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name = 'sister_schema_migrations';
  " | tr -d '[:space:]')" == "1" ]]
}

migration_is_applied() {
  local version="${1:?version required}"
  local escaped_version="${version//\'/\'\'}"

  migration_table_exists || return 1

  [[ "$(db_query "
    SELECT count(*)
    FROM sister_schema_migrations
    WHERE version = '${escaped_version}';
  " | tr -d '[:space:]')" != "0" ]]
}

apply_migration() {
  local migration="${1:?migration required}"
  local filename version

  [[ -f "$migration" ]] || {
    echo "Migration not found: $migration" >&2
    return 1
  }

  filename="$(basename "$migration")"
  version="${filename%.sql}"

  if migration_is_applied "$version"; then
    echo "[SKIP] ${version} already applied to ${SISTER_ENV}"
    return 0
  fi

  echo "[APPLY] ${migration}"
  db_apply_file "$migration"
  echo "[DONE] ${version} applied to ${SISTER_ENV}"
}

if [[ -n "$REQUESTED_MIGRATION" ]]; then
  apply_migration "$REQUESTED_MIGRATION"
  exit 0
fi

mapfile -t migrations < <(
  find storage/migrations \
    -maxdepth 1 \
    -type f \
    -name '*.sql' \
    -print |
  sort -V
)

if [[ ${#migrations[@]} -eq 0 ]]; then
  echo "No migrations found in storage/migrations." >&2
  exit 1
fi

echo "Applying pending SisTer migrations to ${SISTER_ENV}..."

for migration in "${migrations[@]}"; do
  apply_migration "$migration"
done

echo "SisTer migrations are up to date for ${SISTER_ENV}."
