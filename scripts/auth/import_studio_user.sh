#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" != "--reset" || -z "${2:-}" || -n "${3:-}" ]]; then
  echo "Usage: $0 --reset <studio-email>" >&2
  exit 2
fi

EMAIL="$2"
if [[ ! "$EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
  echo "Invalid email." >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AUTH_FILE="${SISTER_AUTH_FILE:-$ROOT_DIR/.run/auth-users.tsv}"
STUDIO_DB_CONTAINER="${SISTER_STUDIO_DB_CONTAINER:-pocket_tts_postgres}"

cd "$ROOT_DIR"

if ! command -v podman >/dev/null 2>&1 ||
   ! podman container exists "$STUDIO_DB_CONTAINER"
then
  echo "Sister-Studio database container is unavailable." >&2
  exit 1
fi

ROW="$(
  podman exec "$STUDIO_DB_CONTAINER" \
    psql -U pocket_tts -d pocket_tts -At -F $'\t' \
    -c "SELECT user_id,name,email,role FROM users WHERE lower(email)=lower('$EMAIL') AND status='active';"
)"
if [[ -z "$ROW" || "$ROW" == *$'\n'* ]]; then
  echo "Expected exactly one active Sister-Studio account for $EMAIL." >&2
  exit 1
fi
IFS=$'\t' read -r USER_ID NAME STORED_EMAIL ROLE <<<"$ROW"

cmake -S . -B build
cmake --build build --target sisterctl
./scripts/app/stop.sh dev

mkdir -p "$(dirname "$AUTH_FILE")"
BACKUP_FILE=""
if [[ -f "$AUTH_FILE" ]]; then
  BACKUP_FILE="${AUTH_FILE}.backup-$(date +%Y%m%d-%H%M%S)"
  mv "$AUTH_FILE" "$BACKUP_FILE"
fi

restore_previous_store() {
  local result=$?
  if [[ "$result" -ne 0 && -n "$BACKUP_FILE" && -f "$BACKUP_FILE" ]]; then
    rm -f "$AUTH_FILE"
    mv "$BACKUP_FILE" "$AUTH_FILE"
    echo "Previous SisTer authentication store restored." >&2
  fi
  ./scripts/app/serve.sh dev 8000 >/dev/null 2>&1 || true
  exit "$result"
}
trap restore_previous_store ERR INT TERM

./build/apps/sisterctl/sisterctl \
  auth-import-user "$USER_ID" "$NAME" "$STORED_EMAIL" "$ROLE"

./scripts/app/serve.sh dev 8000
trap - ERR INT TERM

echo "SisTer identity reset from Sister-Studio account: $STORED_EMAIL"
if [[ -n "$BACKUP_FILE" ]]; then
  echo "Recoverable previous store: $BACKUP_FILE"
fi
