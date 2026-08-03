#!/usr/bin/env python3
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference/sister-reference/server.py"
MANIFEST = ROOT / "reference/sister-reference/manifest.json"
INTERFACE = ROOT / "contracts/subsystem/1.0.0/interface.json"
TOKEN = "contract-test-token-" + "x" * 48


def reserve_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def request(port: int, method: str, path: str, body=None, trusted=False):
    headers = {"Accept": "application/json"}
    if trusted:
        headers.update({
            "X-Sister-Proxy-Token": TOKEN,
            "X-Sister-Subject": "contract-subject",
            "X-Sister-Name": "Contract User",
            "X-Sister-Email": "contract@test.invalid",
            "X-Sister-Role": "admin",
            "X-Request-ID": "contract-request",
        })
    if body is not None:
        body = json.dumps(body)
        headers["Content-Type"] = "application/json"
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    payload = response.read()
    connection.close()
    return response.status, json.loads(payload)


def main() -> None:
    descriptor = json.loads(INTERFACE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = {item["name"]: item["path"] for item in descriptor["endpoints"]}
    assert descriptor["contract"] == manifest["contract"] == "sister.subsystem/1.0.0"
    assert manifest["technical_endpoints"] == expected
    assert descriptor["transport"]["public_listener_prohibited"] is True
    assert manifest["production_eligible"] is False
    jsonschema.validate(manifest, json.loads(
        (INTERFACE.parent / "manifest.schema.json").read_text(encoding="utf-8")))

    port = reserve_port()
    environment = os.environ.copy()
    environment.update({
        "SISTER_REFERENCE_PORT": str(port),
        "SISTER_REFERENCE_MODE": "healthy",
        "SISTER_INTERNAL_PROXY_TOKEN": TOKEN,
    })
    process = subprocess.Popen(
        [sys.executable, str(REFERENCE)], env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                if request(port, "GET", "/health")[0] == 200:
                    break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError("reference did not become healthy")

        for item in descriptor["endpoints"]:
            body = {"value": "contract"} if item["name"] == "echo" else None
            trusted = item["authentication"] == "sister_internal_proxy"
            status, payload = request(port, item["method"], item["path"], body, trusted)
            assert status == item["success_status"], (item, status, payload)
            jsonschema.validate(payload, json.loads(
                (INTERFACE.parent / item["response_schema"]).read_text(encoding="utf-8")))
        assert request(port, "GET", "/identity")[0] == 401
        assert request(port, "POST", "/echo", {"value": "x"})[0] == 401
        assert request(port, "POST", "/echo", {"wrong": "x"}, True)[0] == 400
        assert request(port, "GET", "/unknown")[0] == 404
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=5)
    print("reference_subsystem_contract_tests ok")


if __name__ == "__main__":
    main()
