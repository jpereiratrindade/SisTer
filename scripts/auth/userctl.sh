#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENVIRONMENT="dev"
COMMAND=""

usage() {
  cat <<'EOF'
SisTer local user administration

Usage:
  scripts/auth/userctl.sh [--environment dev|test] list
  scripts/auth/userctl.sh [--environment dev|test] show EMAIL
  scripts/auth/userctl.sh [--environment dev|test] create EMAIL NAME [ROLE]
  scripts/auth/userctl.sh [--environment dev|test] password EMAIL
  scripts/auth/userctl.sh [--environment dev|test] role EMAIL ROLE
  scripts/auth/userctl.sh [--environment dev|test] activate EMAIL
  scripts/auth/userctl.sh [--environment dev|test] deactivate EMAIL
  scripts/auth/userctl.sh [--environment dev|test] revoke-sessions EMAIL
  scripts/auth/userctl.sh [--environment dev|test] sync-runtime [AUTH_FILE]

Roles: guest, registered_user, researcher, project_lead, admin, user
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment) ENVIRONMENT="${2:?missing environment}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) COMMAND="$1"; shift; break ;;
  esac
done

[[ -n "$COMMAND" ]] || { usage >&2; exit 2; }
cd "$ROOT_DIR"
# shellcheck source=../lib/sister_env.sh
source scripts/lib/sister_env.sh
sister_load_env "$ENVIRONMENT"

case "$ENVIRONMENT" in dev|test) ;; *) echo "invalid environment" >&2; exit 2;; esac

psql_cmd() {
  podman exec -i "$SISTER_DB_CONTAINER" sh -lc \
    'psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' "$@"
}

sql_quote() { printf "%s" "$1" | sed "s/'/''/g"; }
normalize_email() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | xargs; }
valid_role() { [[ "$1" =~ ^(guest|registered_user|researcher|project_lead|admin|user)$ ]]; }
read_password() {
  local first second
  read -r -s -p 'Nova senha: ' first; printf '\n'
  read -r -s -p 'Confirme a senha: ' second; printf '\n'
  [[ "$first" == "$second" ]] || { echo 'As senhas não coincidem.' >&2; exit 1; }
  [[ ${#first} -ge 8 ]] || { echo 'A senha precisa ter ao menos 8 caracteres.' >&2; exit 1; }
  PASSWORD="$first"
}
make_credentials() {
  read -r SALT HASH < <(PASSWORD_VALUE="$PASSWORD" python3 - <<'PY'
import hashlib, os
password = os.environ['PASSWORD_VALUE'].encode()
salt = os.urandom(16)
print(salt.hex(), hashlib.pbkdf2_hmac('sha256', password, salt, 210000, 32).hex())
PY
)
}
ensure_migration() {
  podman exec -i "$SISTER_DB_CONTAINER" sh -lc \
    'psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    < storage/migrations/011_local_auth_credentials.sql >/dev/null
}

ensure_migration
case "$COMMAND" in
  list)
    psql_cmd <<'SQL'
SELECT user_id, email, full_name, global_role, active,
       password_hash IS NOT NULL AS password_set, updated_at
FROM sister_users ORDER BY email;
SQL
    ;;
  show)
    email="$(normalize_email "${1:?email required}")"; q="$(sql_quote "$email")"
    psql_cmd <<SQL
SELECT user_id, email, full_name, global_role, active,
       password_hash IS NOT NULL AS password_set, created_at, updated_at
FROM sister_users WHERE lower(email)=lower('$q');
SQL
    ;;
  create)
    email="$(normalize_email "${1:?email required}")"; name="${2:?name required}"; role="${3:-user}"
    valid_role "$role" || { echo "invalid role: $role" >&2; exit 2; }
    read_password; make_credentials
    id="$(python3 - <<'PY'
import uuid; print(uuid.uuid4())
PY
)"
    qe="$(sql_quote "$email")"; qn="$(sql_quote "$name")"; qr="$(sql_quote "$role")"
    psql_cmd <<SQL
INSERT INTO sister_users
(user_id,email,full_name,global_role,password_salt,password_hash,password_iterations,active,updated_at)
VALUES ('$id','$qe','$qn','$qr','$SALT','$HASH',210000,true,now())
ON CONFLICT (email) DO UPDATE SET
 full_name=excluded.full_name, global_role=excluded.global_role,
 password_salt=excluded.password_salt, password_hash=excluded.password_hash,
 password_iterations=excluded.password_iterations, active=true, updated_at=now();
SQL
    ;;
  password)
    email="$(normalize_email "${1:?email required}")"; read_password; make_credentials; q="$(sql_quote "$email")"
    psql_cmd <<SQL
UPDATE sister_users SET password_salt='$SALT', password_hash='$HASH',
 password_iterations=210000, active=true, updated_at=now()
WHERE lower(email)=lower('$q');
DELETE FROM sister_sessions WHERE user_id IN
 (SELECT user_id FROM sister_users WHERE lower(email)=lower('$q'));
SQL
    ;;
  role)
    email="$(normalize_email "${1:?email required}")"; role="${2:?role required}"
    valid_role "$role" || { echo "invalid role: $role" >&2; exit 2; }; qe="$(sql_quote "$email")"
    psql_cmd <<SQL
UPDATE sister_users SET global_role='$(sql_quote "$role")', updated_at=now()
WHERE lower(email)=lower('$qe');
SQL
    ;;
  activate|deactivate)
    email="$(normalize_email "${1:?email required}")"; qe="$(sql_quote "$email")"
    value=true; [[ "$COMMAND" == deactivate ]] && value=false
    psql_cmd <<SQL
UPDATE sister_users SET active=$value, updated_at=now() WHERE lower(email)=lower('$qe');
$( [[ "$COMMAND" == deactivate ]] && printf "UPDATE sister_sessions SET revoked_at=now() WHERE user_id IN (SELECT user_id FROM sister_users WHERE lower(email)=lower('%s')) AND revoked_at IS NULL;" "$qe" )
SQL
    ;;
  revoke-sessions)
    email="$(normalize_email "${1:?email required}")"; qe="$(sql_quote "$email")"
    psql_cmd <<SQL
UPDATE sister_sessions SET revoked_at=now()
WHERE user_id IN (SELECT user_id FROM sister_users WHERE lower(email)=lower('$qe'))
  AND revoked_at IS NULL;
SQL
    ;;
  sync-runtime)
    auth_file="${1:-$ROOT_DIR/.run/gateway/auth-users.tsv}"
    mkdir -p "$(dirname "$auth_file")"
    tmp="${auth_file}.tmp"
    podman exec "$SISTER_DB_CONTAINER" sh -lc \
      'psql -X -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        SELECT concat_ws(
          chr(9),
          user_id::text,
          full_name,
          email,
          CASE
            WHEN global_role IN ('"'"'admin'"'"', '"'"'user'"'"') THEN global_role
            ELSE '"'"'user'"'"'
          END,
          password_salt,
          password_hash
        )
        FROM sister_users
        WHERE active
          AND password_hash IS NOT NULL
        ORDER BY email;
      "' \
      > "$tmp"
    chmod 600 "$tmp"; mv "$tmp" "$auth_file"
    rm -f "${auth_file}.sessions"
    echo "Runtime auth cache updated: $auth_file"
    ;;
  *) usage >&2; exit 2 ;;
esac
