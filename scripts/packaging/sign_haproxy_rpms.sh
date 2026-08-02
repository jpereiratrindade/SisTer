#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SIGNING_HOME="${GNUPGHOME:-$ROOT_DIR/.run/packaging/haproxy/gnupg}"
FINGERPRINT="${HAPROXY_SIGNING_FINGERPRINT:-}"
PUBLIC_KEY="$ROOT_DIR/.run/packaging/haproxy/sister-sec03v-rpm-signing.asc"

if [[ "$#" -lt 1 ]]; then
  echo "Usage: HAPROXY_SIGNING_FINGERPRINT=<full fingerprint> $0 package.rpm [...]" >&2
  exit 2
fi
if [[ -z "$FINGERPRINT" ]]; then
  echo "HAPROXY_SIGNING_FINGERPRINT is required" >&2
  exit 2
fi
FINGERPRINT="${FINGERPRINT^^}"
if [[ ! "$FINGERPRINT" =~ ^[0-9A-F]{40}$ ]]; then
  echo "HAPROXY_SIGNING_FINGERPRINT must be the full 40-hex fingerprint" >&2
  exit 2
fi
for command_name in gpg rpmsign rpmkeys; do
  command -v "$command_name" >/dev/null || {
    echo "Required command is unavailable: $command_name" >&2
    exit 1
  }
done
[[ -d "$SIGNING_HOME" ]] || {
  echo "Dedicated signing keyring does not exist: $SIGNING_HOME" >&2
  exit 1
}

canonical_fingerprint="$(GNUPGHOME="$SIGNING_HOME" gpg --batch --with-colons \
  --list-secret-keys "$FINGERPRINT" | awk -F: '$1 == "fpr" { print $10; exit }')"
if [[ "$canonical_fingerprint" != "$FINGERPRINT" ]]; then
  echo "The requested full fingerprint does not identify the dedicated secret key" >&2
  exit 1
fi

GNUPGHOME="$SIGNING_HOME" gpg --armor --export "$FINGERPRINT" > "$PUBLIC_KEY"
chmod 0600 "$PUBLIC_KEY"

for package in "$@"; do
  [[ -f "$package" ]] || {
    echo "Package does not exist: $package" >&2
    exit 1
  }
  GNUPGHOME="$SIGNING_HOME" rpmsign --addsign \
    --define "_gpg_path $SIGNING_HOME" \
    --define "_gpg_name $FINGERPRINT" \
    --define "_openpgp_sign_id $FINGERPRINT" \
    "$package"
done

verification_db="$(mktemp -d "$ROOT_DIR/.run/packaging/haproxy/rpmdb.XXXXXX")"
cleanup() {
  rm -r "$verification_db"
}
trap cleanup EXIT
rpm --dbpath "$verification_db" --initdb
rpmkeys --dbpath "$verification_db" --import "$PUBLIC_KEY"
for package in "$@"; do
  rpmkeys --dbpath "$verification_db" --checksig --verbose "$package"
done

echo "Packages signed and verified with: $FINGERPRINT"
echo "Public key: $PUBLIC_KEY"
