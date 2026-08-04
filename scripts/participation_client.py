#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    if len(sys.argv) not in {3, 4} or sys.argv[1] not in {"propose", "show"}:
        print("usage: participation_client.py propose <contract.json> [--json] | show <id> [--json]", file=sys.stderr)
        return 2
    base = os.environ.get("SISTER_API_URL", "http://127.0.0.1:8000").rstrip("/")
    cookie = os.environ.get("SISTER_SESSION_COOKIE")
    if not cookie:
        print("participation error: SISTER_SESSION_COOKIE must contain an authenticated session", file=sys.stderr)
        return 1
    as_json = len(sys.argv) == 4 and sys.argv[3] == "--json"
    if sys.argv[1] == "propose":
        contract = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        raw = json.dumps(contract, ensure_ascii=False, separators=(",", ":")).encode()
        payload = dict(contract)
        payload["contract_version"] = "1.0.0"
        payload["contract_digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
        payload["origin_commit"] = os.environ.get("SISTER_ORIGIN_COMMIT", "unrecorded")
        body = json.dumps(payload, ensure_ascii=False).encode()
        url = base + "/api/v1/participations"
        method = "POST"
    else:
        url = base + "/api/v1/participations/" + urllib.parse.quote(sys.argv[2], safe="")
        body = None
        method = "GET"
    request = urllib.request.Request(url, data=body, method=method, headers={"Cookie": cookie, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read())
            print(json.dumps(result, ensure_ascii=False, indent=2) if as_json else f"{result.get('participation_id', sys.argv[2])} [{result.get('state', 'unknown')}]")
            return 0
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        print(f"participation error: HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(f"participation error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
