#!/usr/bin/env python3
import copy
import os
from pathlib import Path
import shutil
import stat
import sys
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_gateway_config import (  # noqa: E402
    RenderError,
    TEMPLATE_PATH,
    checked_environment,
    render,
    validate_governed_profile,
    write_private_atomic,
)


def expect_rejected(environment, fragment, scope="lab"):
    try:
        checked_environment(environment, scope)
    except RenderError as exc:
        assert fragment in str(exc), (fragment, str(exc))
        return
    raise AssertionError(f"unsafe environment accepted; expected {fragment!r}")


def main():
    temporary = ROOT / ".run/gateway" / f"render-test-{uuid.uuid4().hex}"
    temporary.mkdir(mode=0o700, parents=True)
    try:
        pem = temporary / "gateway-lab.pem"
        pem.write_text("test-only-placeholder\n", encoding="utf-8")
        pem.chmod(0o600)
        fake_haproxy = temporary / "haproxy"
        fake_haproxy.write_text(
            "#!/usr/bin/env sh\nprintf '%s\\n' 'HAProxy version 3.2.22 2026/07/29'\n",
            encoding="utf-8",
        )
        fake_haproxy.chmod(0o700)
        environment = {
            "GATEWAY_TLS_PEM": str(pem),
            "GATEWAY_ALLOWED_HOST": "sister-gateway.test",
            "GATEWAY_CANONICAL_HOST": "sister-gateway.test",
            "GATEWAY_HAPROXY_BIN": str(fake_haproxy),
        }

        validate_governed_profile(ROOT / "ops/gateway/security-profile.json")
        values = checked_environment(environment)
        rendered = render(TEMPLATE_PATH.read_text(encoding="utf-8"), values)
        assert "@@" not in rendered
        assert "bind 127.0.0.1:8443" in rendered
        assert f"server sisterd unix@{ROOT}/.run/gateway/sisterd.sock check" in rendered
        assert "http-request del-header X-Sister- -m beg" in rendered
        assert "alpn http/1.1" in rendered
        assert "strict-sni" in rendered
        assert "http-request set-header Host sister-gateway.test" in rendered
        assert "sister-gateway.test:8443" in rendered
        assert "http-request deny status 400 if HTTP_URL_ABS" in rendered
        assert "tune.stick-counters 5" in rendered
        assert "tcp-request connection reject if { sc_conn_cur(0) gt 32 }" in rendered
        assert rendered.count("http-request track-sc") == 4
        assert rendered.count("status 429") == 4
        assert "hdr Retry-After 60" in rendered
        assert "maxconn 32 maxqueue 64" in rendered
        assert "stats socket " in rendered and "mode 600 level operator" in rendered
        assert '"queue_ms":%Tw' in rendered
        assert '"upstream_ms":%Tr' in rendered
        assert "lua" not in rendered.lower()

        lan_environment = copy.deepcopy(environment)
        lan_environment["GATEWAY_LISTEN_ADDRESS"] = "10.163.80.176"
        lan_values = checked_environment(lan_environment, "lan-lab")
        lan_rendered = render(TEMPLATE_PATH.read_text(encoding="utf-8"), lan_values)
        assert "bind 10.163.80.176:8443" in lan_rendered
        assert f"server sisterd unix@{ROOT}/.run/gateway/sisterd.sock check" in lan_rendered
        isolated_environment = copy.deepcopy(environment)
        isolated_root = temporary / "isolated-runtime"
        isolated_root.mkdir(mode=0o700)
        isolated_pem = isolated_root / "gateway-lab.pem"
        isolated_pem.write_text("test-only-placeholder\n", encoding="utf-8")
        isolated_pem.chmod(0o600)
        isolated_environment["GATEWAY_RUN_ROOT"] = str(isolated_root)
        isolated_environment["GATEWAY_TLS_PEM"] = str(isolated_pem)
        isolated_values = checked_environment(isolated_environment)
        isolated_rendered = render(TEMPLATE_PATH.read_text(encoding="utf-8"), isolated_values)
        assert f"server sisterd unix@{isolated_root}/sisterd.sock check" in isolated_rendered
        assert f"stats socket {isolated_root}/haproxy.sock" in isolated_rendered
        for address in ("127.0.0.1", "0.0.0.0", "192.0.2.10", "not-an-ip"):
            changed = copy.deepcopy(environment)
            changed["GATEWAY_LISTEN_ADDRESS"] = address
            expect_rejected(changed, "lan-lab listener", "lan-lab")

        output = temporary / "haproxy.cfg"
        write_private_atomic(output, rendered)
        assert stat.S_IMODE(output.stat().st_mode) == 0o640

        unsafe_cases = (
            ("GATEWAY_LISTEN_ADDRESS", "0.0.0.0", "listener must be 127.0.0.1"),
            ("GATEWAY_LISTEN_PORT", "443", "port must be 8443"),
            ("GATEWAY_UPSTREAM_SOCKET", "/tmp/sisterd.sock", "must remain inside"),
            ("GATEWAY_UPSTREAM_ADDRESS", "127.0.0.1", "TCP upstream configuration is forbidden"),
            ("GATEWAY_UPSTREAM_PORT", "8000", "TCP upstream configuration is forbidden"),
            ("GATEWAY_ALLOWED_HOST", "*.test", "one exact DNS name"),
            ("GATEWAY_CANONICAL_HOST", "other.test", "must match"),
        )
        for name, replacement, fragment in unsafe_cases:
            changed = copy.deepcopy(environment)
            changed[name] = replacement
            expect_rejected(changed, fragment)

        permissive_pem = temporary / "permissive.pem"
        permissive_pem.write_text("test-only-placeholder\n", encoding="utf-8")
        permissive_pem.chmod(0o644)
        changed = copy.deepcopy(environment)
        changed["GATEWAY_TLS_PEM"] = str(permissive_pem)
        expect_rejected(changed, "0600 or stricter")

        old_haproxy = temporary / "haproxy-old"
        old_haproxy.write_text("#!/usr/bin/env sh\necho 'HAProxy version 3.2.21'\n", encoding="utf-8")
        old_haproxy.chmod(0o700)
        changed = copy.deepcopy(environment)
        changed["GATEWAY_HAPROXY_BIN"] = str(old_haproxy)
        expect_rejected(changed, "3.2.22 or newer")

        try:
            render(TEMPLATE_PATH.read_text(encoding="utf-8") + "\nlua-load /tmp/unsafe.lua\n", values)
        except RenderError:
            pass
        else:
            raise AssertionError("Lua directive was accepted")
    finally:
        shutil.rmtree(temporary)

    print("gateway_config_render_tests ok")


if __name__ == "__main__":
    main()
