#!/usr/bin/env bash

if [[ -f ".env" ]]; then
  set -a
  source ".env"
  set +a
fi

sister_load_env() {
  local env_name="${1:-dev}"
  if [[ -z "${SISTER_DB_PASSWORD:-}" ]]; then
    echo "Error: SISTER_DB_PASSWORD must be set in .env" >&2
    return 1
  fi

  case "$env_name" in
    dev)
      export SISTER_ENV="dev"
      export COMPOSE_PROJECT_NAME="sister-dev"
      export SISTER_DB_CONTAINER="sister-dev-db"
      export SISTER_DB_PORT="${SISTER_DEV_DB_PORT:-55434}"
      export SISTER_DB_VOLUME="sister_dev_pgdata"
      export SISTER_DATABASE_URL="${SISTER_DEV_DATABASE_URL:-postgresql://sister:${SISTER_DB_PASSWORD}@localhost:${SISTER_DB_PORT}/sister}"
      export SISTER_APP_PORT="${SISTER_DEV_APP_PORT:-8000}"
      export SISTER_BIND_HOST="${SISTER_DEV_BIND_HOST:-127.0.0.1}"
      ;;
    test)
      export SISTER_ENV="test"
      export COMPOSE_PROJECT_NAME="sister-test"
      export SISTER_DB_CONTAINER="sister-test-db"
      export SISTER_DB_PORT="${SISTER_TEST_DB_PORT:-55435}"
      export SISTER_DB_VOLUME="sister_test_pgdata"
      export SISTER_DATABASE_URL="${SISTER_TEST_DATABASE_URL:-postgresql://sister:${SISTER_DB_PASSWORD}@localhost:${SISTER_DB_PORT}/sister}"
      export SISTER_APP_PORT="${SISTER_TEST_APP_PORT:-8001}"
      export SISTER_BIND_HOST="${SISTER_TEST_BIND_HOST:-127.0.0.1}"
      ;;
    *)
      echo "Unknown SisTer environment: $env_name" >&2
      echo "Expected: dev or test" >&2
      return 1
      ;;
  esac
}

sister_print_env() {
  cat <<MSG
SisTer environment: ${SISTER_ENV}
  COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
  SISTER_DB_CONTAINER=${SISTER_DB_CONTAINER}
  SISTER_DB_PORT=${SISTER_DB_PORT}
  SISTER_DB_VOLUME=${SISTER_DB_VOLUME}
  SISTER_DATABASE_URL=<configured; credentials redacted>
  SISTER_APP_PORT=${SISTER_APP_PORT}
  SISTER_BIND_HOST=${SISTER_BIND_HOST}
MSG
}
