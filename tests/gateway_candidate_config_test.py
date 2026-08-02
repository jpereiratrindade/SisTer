#!/usr/bin/env python3
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import render_gateway_config as renderer  # noqa: E402


def main():
    temporary = Path(tempfile.mkdtemp(prefix="sec03v-candidate-"))
    try:
        etc_root = temporary / "etc/sister/gateway"
        run_root = temporary / "run"
        etc_root.mkdir(parents=True)
        (etc_root / "errors").mkdir()
        pem = etc_root / "tls.pem"
        pem.write_text("test-only-placeholder\n", encoding="utf-8")
        pem.chmod(0o640)
        fake_haproxy = temporary / "haproxy-3.2.22"
        fake_haproxy.write_text(
            "#!/usr/bin/env sh\nprintf '%s\\n' 'HAProxy version 3.2.22 2026/07/29'\n",
            encoding="utf-8",
        )
        fake_haproxy.chmod(0o700)

        renderer.CANDIDATE_CONFIG = etc_root / "haproxy.cfg"
        renderer.CANDIDATE_TLS_PEM = pem
        renderer.CANDIDATE_ERROR_ROOT = etc_root / "errors"
        renderer.CANDIDATE_STATS_SOCKET = run_root / "sister-gateway/haproxy.sock"
        renderer.CANDIDATE_UPSTREAM_SOCKET = run_root / "sister/sisterd.sock"

        environment = {
            "GATEWAY_TLS_PEM": str(pem),
            "GATEWAY_ALLOWED_HOST": "sister-gateway.test",
            "GATEWAY_CANONICAL_HOST": "sister-gateway.test",
            "GATEWAY_HAPROXY_BIN": str(fake_haproxy),
            "GATEWAY_UPSTREAM_SOCKET": str(renderer.CANDIDATE_UPSTREAM_SOCKET),
        }
        values = renderer.checked_environment(environment, "candidate")
        rendered = renderer.render(renderer.TEMPLATE_PATH.read_text(encoding="utf-8"), values)
        assert f"unix@{renderer.CANDIDATE_UPSTREAM_SOCKET}" in rendered
        assert str(renderer.CANDIDATE_ERROR_ROOT) in rendered
        assert str(renderer.CANDIDATE_STATS_SOCKET) in rendered
        assert "bind 127.0.0.1:8443" in rendered
        renderer.write_private_atomic(renderer.CANDIDATE_CONFIG, rendered, "candidate")
        assert stat.S_IMODE(renderer.CANDIDATE_CONFIG.stat().st_mode) == 0o640

        changed = environment.copy()
        changed["GATEWAY_UPSTREAM_SOCKET"] = "/tmp/unsafe.sock"
        try:
            renderer.checked_environment(changed, "candidate")
        except renderer.RenderError as error:
            assert "candidate upstream" in str(error)
        else:
            raise AssertionError("candidate accepted a non-governed upstream")
    finally:
        shutil.rmtree(temporary)

    print("gateway_candidate_config_tests ok")


if __name__ == "__main__":
    main()
