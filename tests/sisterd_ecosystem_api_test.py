#!/usr/bin/env python3
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time


def reserve_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def request(port, method, path, body=None, cookie=None):
    headers = {"Accept": "application/json"}
    if body is not None:
        body = json.dumps(body)
        headers["Content-Type"] = "application/json"
    if cookie:
        headers["Cookie"] = cookie
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    payload = response.read()
    result = response.status, dict(response.getheaders()), payload
    connection.close()
    return result


def wait_for_server(port, process):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("sisterd exited before accepting requests")
        try:
            if request(port, "GET", "/api/health")[0] == 200:
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("sisterd did not become ready")


def run_mock_health_server(port, stop_event, ready_event, probe_path="/api/health"):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
        listener.listen(4)
        listener.settimeout(0.2)
        ready_event.set()
        while not stop_event.is_set():
            try:
                connection, _ = listener.accept()
            except socket.timeout:
                continue
            with connection:
                raw = b""
                while b"\r\n\r\n" not in raw:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    raw += chunk
                body = b'{"status":"ok"}'
                connection.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: application/json\r\n"
                    + f"Content-Length: {len(body)}\r\n".encode("ascii")
                    + b"Connection: close\r\n\r\n"
                    + body
                )


def write_projection(path, meta, participants):
    lines = [
        f"META\t{meta.get('composition_id', '')}\t{meta.get('deployment_id', '')}\t{meta.get('status', 'READY')}"
    ]
    for p in participants:
        lines.append(
            f"PARTICIPANT\t{p['component_id']}\t{p['system_id']}\t{p['transport']}\t{p['listen']}\t{p['port']}\t{p['health_path']}\t{p.get('gateway_host', '')}\t{p.get('gateway_public_url', '')}"
        )
        for surface in p.get("interaction_surfaces", []):
            lines.append(
                f"SURFACE\t{p['component_id']}\t{surface['surface_id']}\t{surface['label']}\t{surface['purpose']}\t{surface.get('public_url', '')}\t{surface['access_class']}"
            )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    executable, web_root = sys.argv[1:3]
    sister_port = reserve_port()
    alpha_port = reserve_port()
    gamma_port = reserve_port()
    beta_port = reserve_port()  # Beta will NOT have a running mock server (simulates offline)

    stop_event = threading.Event()
    alpha_ready = threading.Event()
    gamma_ready = threading.Event()

    alpha_mock = threading.Thread(
        target=run_mock_health_server,
        args=(alpha_port, stop_event, alpha_ready, "/api/health"),
        daemon=True,
    )
    gamma_mock = threading.Thread(
        target=run_mock_health_server,
        args=(gamma_port, stop_event, gamma_ready, "/health"),
        daemon=True,
    )

    alpha_mock.start()
    gamma_mock.start()
    assert alpha_ready.wait(timeout=2)
    assert gamma_ready.wait(timeout=2)

    with tempfile.TemporaryDirectory(prefix="sister-ecosystem-test-") as temporary:
        projection_file = Path(temporary) / "projection.tsv"
        auth_file = Path(temporary) / "auth.tsv"

        # WEB-08: Initial 3 fixtures: alpha (online, published), beta (offline, published), gamma (online, not published)
        initial_participants = [
            {
                "component_id": "alpha",
                "system_id": "participant_alpha",
                "transport": "tcp",
                "listen": "127.0.0.1",
                "port": alpha_port,
                "health_path": "/api/health",
                "gateway_host": "alpha-gateway.test",
                "gateway_public_url": "https://alpha-gateway.test:9443",
                "interaction_surfaces": [{
                    "surface_id": "alpha-work",
                    "label": "Alpha",
                    "purpose": "Executar trabalho Alpha",
                    "public_url": "https://alpha-gateway.test:9443",
                    "access_class": "authenticated",
                }],
            },
            {
                "component_id": "beta",
                "system_id": "participant_beta",
                "transport": "tcp",
                "listen": "127.0.0.1",
                "port": beta_port,
                "health_path": "/api/health",
                "gateway_host": "beta-gateway.test",
                "gateway_public_url": "https://beta-gateway.test:9443",
                "interaction_surfaces": [{
                    "surface_id": "beta-admin",
                    "label": "Beta Admin",
                    "purpose": "Administrar Beta",
                    "public_url": "https://beta-gateway.test:9443",
                    "access_class": "engineering",
                }],
            },
            {
                "component_id": "gamma",
                "system_id": "participant_gamma",
                "transport": "tcp",
                "listen": "127.0.0.1",
                "port": gamma_port,
                "health_path": "/health",
                "gateway_host": "",
                "gateway_public_url": "",
            },
        ]
        meta = {
            "composition_id": "test-composition",
            "deployment_id": "test-deployment",
            "status": "READY",
        }
        write_projection(projection_file, meta, initial_participants)

        environment = os.environ.copy()
        environment.update({
            "SISTER_ENV": "development",
            "SISTER_BIND_HOST": "127.0.0.1",
            "SISTER_AUTH_FILE": str(auth_file),
            "SISTER_DATABASE_URL": "",
            "SISTER_COOKIE_SECURE": "false",
            "SISTER_ECOSYSTEM_PROJECTION_FILE": str(projection_file),
            "SISTER_SUBSYSTEM_HEALTH_TIMEOUT_MS": "300",
        })

        process = subprocess.Popen(
            [executable, str(sister_port), web_root],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            wait_for_server(sister_port, process)

            # Register user to get session cookie
            status, headers, payload = request(sister_port, "POST", "/api/auth/register", {
                "name": "Ecosystem Admin",
                "email": "ecosystem-admin@test.invalid",
                "password": "ecosystem-test-password-123",
            })
            assert status == 201, (status, payload)
            cookie = headers["Set-Cookie"].split(";", 1)[0]

            status, _, _ = request(sister_port, "POST", "/api/admin/users", {
                "name": "Workspace User",
                "email": "workspace-user@test.invalid",
                "password": "workspace-user-password",
                "role": "user",
            }, cookie)
            assert status == 201, status
            status, headers, _ = request(sister_port, "POST", "/api/auth/login", {
                "email": "workspace-user@test.invalid",
                "password": "workspace-user-password",
            })
            assert status == 200, status
            user_cookie = headers["Set-Cookie"].split(";", 1)[0]

            status, _, workspace_payload = request(
                sister_port, "GET", "/api/v1/workspace", cookie=user_cookie
            )
            assert status == 200, (status, workspace_payload)
            workspace = json.loads(workspace_payload)
            assert workspace["schema"] == "sister.workspace-view/1.0.0"
            assert [surface["surface_id"] for surface in workspace["surfaces"]] == ["alpha-work"]
            assert workspace["surfaces"][0]["participant_id"] == "participant_alpha"
            assert workspace["surfaces"][0]["public_url"] == "https://alpha-gateway.test:9443"
            serialized_workspace = json.dumps(workspace)
            for internal_field in ("runtime", "listen", "port", "probe", "health_path", "deployment"):
                assert internal_field not in serialized_workspace, serialized_workspace

            status, _, admin_workspace_payload = request(
                sister_port, "GET", "/api/v1/workspace", cookie=cookie
            )
            assert status == 200
            assert [surface["surface_id"] for surface in json.loads(admin_workspace_payload)["surfaces"]] == [
                "alpha-work", "beta-admin"
            ]

            assert request(sister_port, "GET", "/api/ecosystem", cookie=user_cookie)[0] == 403
            assert request(sister_port, "GET", "/engineering/", cookie=user_cookie)[0] == 403
            assert request(sister_port, "GET", "/engineering/app.js", cookie=user_cookie)[0] == 403
            assert request(sister_port, "GET", "/engineering/", cookie=cookie)[0] == 200

            # WEB-08: Test GET /api/ecosystem
            status, _, payload = request(sister_port, "GET", "/api/ecosystem", cookie=cookie)
            assert status == 200, (status, payload)
            ecosystem = json.loads(payload)

            assert ecosystem["schema"] == "sister.runtime.ecosystem-view/1"
            assert ecosystem["composition_id"] == "test-composition"
            assert ecosystem["deployment_id"] == "test-deployment"
            assert ecosystem["deployment_status"] == "READY"
            assert len(ecosystem["systems"]) == 3, ecosystem

            systems_by_id = {s["component_id"]: s for s in ecosystem["systems"]}
            assert "alpha" in systems_by_id
            assert "beta" in systems_by_id
            assert "gamma" in systems_by_id

            # Check alpha: online, published with public_url
            alpha = systems_by_id["alpha"]
            assert alpha["system_id"] == "participant_alpha"
            assert alpha["health"]["status"] == "online"
            assert alpha["health"]["http_status"] == 200
            assert alpha["health"]["detail"] == "ok"
            assert alpha["gateway"]["host"] == "alpha-gateway.test"
            assert alpha["gateway"]["public_url"] == "https://alpha-gateway.test:9443"

            # Check beta: offline, published with public_url
            beta = systems_by_id["beta"]
            assert beta["system_id"] == "participant_beta"
            assert beta["health"]["status"] == "offline"
            assert beta["gateway"]["host"] == "beta-gateway.test"
            assert beta["gateway"]["public_url"] == "https://beta-gateway.test:9443"

            # Check gamma: online, not published (empty gateway host / public_url)
            gamma = systems_by_id["gamma"]
            assert gamma["system_id"] == "participant_gamma"
            assert gamma["health"]["status"] == "online"
            assert gamma["health"]["http_status"] == 200
            assert gamma["gateway"]["host"] == ""
            assert not gamma["gateway"].get("public_url")

            # Check summary statistics
            participants_count = len(ecosystem["systems"])
            operational_count = sum(1 for s in ecosystem["systems"] if s["health"]["status"] == "online")
            published_count = sum(1 for s in ecosystem["systems"] if bool(s["gateway"].get("host")))
            assert participants_count == 3
            assert operational_count == 2
            assert published_count == 2

            # WEB-04: Test GET /api/systems compatibility
            status, _, sys_payload = request(sister_port, "GET", "/api/systems", cookie=cookie)
            assert status == 200, (status, sys_payload)
            compat_systems = json.loads(sys_payload)
            assert len(compat_systems) == 3
            compat_by_id = {s["component_id"]: s for s in compat_systems}
            assert compat_by_id["alpha"]["health_status"] == "online"
            assert compat_by_id["alpha"]["gateway"]["public_url"] == "https://alpha-gateway.test:9443"
            assert compat_by_id["beta"]["health_status"] == "offline"
            assert compat_by_id["beta"]["gateway"]["public_url"] == "https://beta-gateway.test:9443"
            assert compat_by_id["gamma"]["health_status"] == "online"

            # WEB-09: Extensibility test - add 'delta' only to projection file without code modification
            delta_port = reserve_port()
            delta_ready = threading.Event()
            delta_mock = threading.Thread(
                target=run_mock_health_server,
                args=(delta_port, stop_event, delta_ready, "/api/health"),
                daemon=True,
            )
            delta_mock.start()
            assert delta_ready.wait(timeout=2)

            extended_participants = initial_participants + [
                {
                    "component_id": "delta",
                    "system_id": "participant_delta",
                    "transport": "tcp",
                    "listen": "127.0.0.1",
                    "port": delta_port,
                    "health_path": "/api/health",
                    "gateway_host": "delta-gateway.test",
                    "gateway_public_url": "https://delta-gateway.test:9443",
                    "interaction_surfaces": [{
                        "surface_id": "delta-work",
                        "label": "Delta",
                        "purpose": "Executar trabalho Delta",
                        "public_url": "https://delta-gateway.test:9443",
                        "access_class": "authenticated",
                    }],
                }
            ]
            write_projection(projection_file, meta, extended_participants)

            # Query /api/ecosystem again
            status, _, payload_delta = request(sister_port, "GET", "/api/ecosystem", cookie=cookie)
            assert status == 200, (status, payload_delta)
            ecosystem_delta = json.loads(payload_delta)
            assert len(ecosystem_delta["systems"]) == 4, ecosystem_delta

            delta_by_id = {s["component_id"]: s for s in ecosystem_delta["systems"]}
            assert "delta" in delta_by_id
            delta = delta_by_id["delta"]
            assert delta["system_id"] == "participant_delta"
            assert delta["health"]["status"] == "online"
            assert delta["gateway"]["host"] == "delta-gateway.test"
            assert delta["gateway"]["public_url"] == "https://delta-gateway.test:9443"

            new_participants_count = len(ecosystem_delta["systems"])
            new_operational_count = sum(1 for s in ecosystem_delta["systems"] if s["health"]["status"] == "online")
            new_published_count = sum(1 for s in ecosystem_delta["systems"] if bool(s["gateway"].get("host")))
            assert new_participants_count == 4
            assert new_operational_count == 3
            assert new_published_count == 3

            status, _, workspace_delta_payload = request(
                sister_port, "GET", "/api/v1/workspace", cookie=user_cookie
            )
            assert status == 200
            assert [surface["surface_id"] for surface in json.loads(workspace_delta_payload)["surfaces"]] == [
                "alpha-work", "delta-work"
            ]

        finally:
            stop_event.set()
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

    # Section 10 & 12: Validate Home frontend rules against URL synthesis
    app_js = (Path(web_root) / "app.js").read_text(encoding="utf-8")
    assert "window.location.port" not in app_js, "app.js sintetiza porta da janela"
    assert "window.location.protocol" not in app_js, "app.js sintetiza protocolo da janela"
    assert ":8443" not in app_js, "app.js contém porta hardcoded"
    assert "surface.public_url" in app_js
    assert "/api/ecosystem" not in app_js

    print("sisterd_ecosystem_api_tests (public_url and delta) ok")


if __name__ == "__main__":
    main()
