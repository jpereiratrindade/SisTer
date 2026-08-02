#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="3.2.22"
IMAGE="registry.fedoraproject.org/fedora:44"
SOURCE="$ROOT_DIR/.run/packaging/haproxy/sources/haproxy-${VERSION}.tar.gz"
OFFICIAL_CHECKSUM="$SOURCE.sha256.official"
SPEC="$ROOT_DIR/packaging/haproxy/haproxy.spec"
RUN_ROOT="$ROOT_DIR/.run/packaging/haproxy"
BUILD_ID="$(date -u +%Y%m%dT%H%M%SZ)"
TOPDIR="$RUN_ROOT/rpmbuild-$BUILD_ID"
RESULTS="$RUN_ROOT/podman-results/$BUILD_ID"

for command_name in podman rpmbuild sha256sum; do
  command -v "$command_name" >/dev/null || {
    echo "Required command is unavailable: $command_name" >&2
    exit 1
  }
done

"$ROOT_DIR/scripts/packaging/prepare_haproxy_source.sh"
install -d -m 0700 \
  "$TOPDIR/BUILD" "$TOPDIR/BUILDROOT" "$TOPDIR/RPMS" \
  "$TOPDIR/SOURCES" "$TOPDIR/SPECS" "$TOPDIR/SRPMS" "$RESULTS"
install -m 0600 "$SOURCE" "$TOPDIR/SOURCES/haproxy-${VERSION}.tar.gz"
install -m 0600 "$OFFICIAL_CHECKSUM" "$RESULTS/$(basename "$OFFICIAL_CHECKSUM")"
install -m 0600 "$SPEC" "$TOPDIR/SPECS/haproxy.spec"

rpmbuild -bs "$TOPDIR/SPECS/haproxy.spec" --define "_topdir $TOPDIR"
srpm="$(find "$TOPDIR/SRPMS" -maxdepth 1 -type f -name '*.src.rpm' -print -quit)"
[[ -n "$srpm" ]] || {
  echo "SRPM was not produced" >&2
  exit 1
}
install -m 0600 "$srpm" "$RESULTS/$(basename "$srpm")"

podman pull "$IMAGE"
image_digest="$(podman image inspect "$IMAGE" --format '{{.Digest}}')"
printf '%s@%s\n' "$IMAGE" "$image_digest" > "$RESULTS/build-environment.txt"

podman run --rm --network=host \
  --security-opt=no-new-privileges \
  -v "$TOPDIR/SRPMS:/input:ro,Z" \
  -v "$RESULTS:/results:Z" \
  "$IMAGE" bash -euo pipefail -c '
    dnf install -y rpm-build gcc libxcrypt-devel make openssl-devel pcre2-devel
    rpm -qa | sort > /results/build-packages.txt
    rpmbuild --rebuild /input/*.src.rpm \
      --define "_rpmdir /results" \
      --define "_srcrpmdir /results"
  ' 2>&1 | tee "$RESULTS/build.log"

rpm_file="$(find "$RESULTS" -type f -name 'sister-haproxy-lab-*.x86_64.rpm' -print -quit)"
[[ -n "$rpm_file" ]] || {
  echo "Binary RPM was not produced" >&2
  exit 1
}
if [[ "$(dirname "$rpm_file")" != "$RESULTS" ]]; then
  install -m 0600 "$rpm_file" "$RESULTS/$(basename "$rpm_file")"
  rpm_file="$RESULTS/$(basename "$rpm_file")"
fi

rpm -qpl "$rpm_file"
if [[ -n "$(rpm -qp --scripts "$rpm_file")" ]]; then
  echo "Unexpected RPM installation scripts" >&2
  exit 1
fi
sha256sum "$RESULTS"/*.rpm > "$RESULTS/SHA256SUMS.unsigned"
chmod -R go-rwx "$TOPDIR" "$RESULTS"

echo "Unsigned isolated build completed: $RESULTS"
