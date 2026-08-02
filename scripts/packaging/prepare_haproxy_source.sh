#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="3.2.22"
SOURCE_NAME="haproxy-${VERSION}.tar.gz"
SOURCE_URL="https://www.haproxy.org/download/3.2/src/${SOURCE_NAME}"
CHECKSUM_URL="${SOURCE_URL}.sha256"
EXPECTED_SHA256="afca3a26d573df53d0e1fc475dcd743ec5875e038e1476c80e871d70228ca2da"
SOURCE_DIR="$ROOT_DIR/.run/packaging/haproxy/sources"
OUTPUT="$SOURCE_DIR/$SOURCE_NAME"
OFFICIAL_CHECKSUM="$SOURCE_DIR/${SOURCE_NAME}.sha256.official"

mkdir -p "$SOURCE_DIR"
chmod 700 "$ROOT_DIR/.run/packaging" "$ROOT_DIR/.run/packaging/haproxy" "$SOURCE_DIR"
umask 077

temporary="$(mktemp "$SOURCE_DIR/${SOURCE_NAME}.download.XXXXXX")"
temporary_checksum="$(mktemp "$SOURCE_DIR/${SOURCE_NAME}.sha256.download.XXXXXX")"
cleanup() {
  rm -f "$temporary" "$temporary_checksum"
}
trap cleanup EXIT

curl --proto '=https' --tlsv1.3 --fail --silent --show-error --location \
  "$CHECKSUM_URL" -o "$temporary_checksum"
published_sha256="$(awk 'NR == 1 { print $1 }' "$temporary_checksum")"
if [[ "$published_sha256" != "$EXPECTED_SHA256" ]]; then
  echo "Published HAProxy checksum differs from the governed value" >&2
  exit 1
fi
curl --proto '=https' --tlsv1.3 --fail --silent --show-error --location \
  "$SOURCE_URL" -o "$temporary"
actual_sha256="$(sha256sum "$temporary" | awk '{print $1}')"
if [[ "$actual_sha256" != "$EXPECTED_SHA256" ]]; then
  echo "HAProxy source checksum mismatch" >&2
  exit 1
fi
tar -tzf "$temporary" >/dev/null
mv -f "$temporary" "$OUTPUT"
mv -f "$temporary_checksum" "$OFFICIAL_CHECKSUM"
chmod 600 "$OUTPUT" "$OFFICIAL_CHECKSUM"
trap - EXIT

echo "Verified upstream source: $OUTPUT"
echo "SHA-256: $actual_sha256"
