#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

if [[ $# -ne 2 ]]; then
  echo "usage: render-ecosystem-projection.sh RESOLVED_DEPLOYMENT OUTPUT" >&2
  exit 2
fi

RESOLVED_DEPLOYMENT="$1"
OUTPUT="$2"

[[ -f "$RESOLVED_DEPLOYMENT" ]] || {
  echo "resolved deployment not found: $RESOLVED_DEPLOYMENT" >&2
  exit 3
}
command -v jq >/dev/null 2>&1 || {
  echo "jq is required to render the ecosystem projection" >&2
  exit 4
}

mkdir -p "$(dirname "$OUTPUT")"
TEMP_OUTPUT="$(mktemp "${OUTPUT}.tmp.XXXXXX")"
trap 'rm -f "$TEMP_OUTPUT"' EXIT

jq -r '
  "META\t" + (.composition_id // "") + "\t" + (.deployment_id // "") + "\t" + (.status // "NOT_CONFIGURED"),
  ( (.components // [])[] as $component |
    ("PARTICIPANT\t" +
      ($component.component_id // "") + "\t" +
      ($component.system_id // "") + "\t" +
      ($component.runtime.transport // "") + "\t" +
      ($component.runtime.listen // "") + "\t" +
      (($component.runtime.port // 0) | tostring) + "\t" +
      ($component.probe.health_path // "") + "\t" +
      ($component.gateway.host // "") + "\t" +
      ($component.gateway.public_url // "")),
    (($component.interaction_surfaces // [])[] |
      "SURFACE\t" +
      ($component.component_id // "") + "\t" +
      (.surface_id // "") + "\t" +
      (.label // "") + "\t" +
      (.purpose // "") + "\t" +
      (.public_url // "") + "\t" +
      (.access_class // ""))
  )
' "$RESOLVED_DEPLOYMENT" > "$TEMP_OUTPUT"

mv "$TEMP_OUTPUT" "$OUTPUT"
trap - EXIT
