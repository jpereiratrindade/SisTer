#!/usr/bin/env python3

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

public_js = (ROOT / "web" / "public.js").read_text(encoding="utf-8")
index_html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

expected_navigation = (
    'href="/_sister/open/${systemKey}">'
    'Explorar ${system.name}</a>'
)

if expected_navigation not in public_js:
    raise SystemExit(
        "FAIL: public subsystem CTA is not routed through "
        "/_sister/open/<component_id>"
    )

forbidden = (
    'href="/login">Entrar para acessar ${system.name}</a>'
)

if forbidden in public_js:
    raise SystemExit(
        "FAIL: public subsystem exploration still requires SisTer login"
    )

for component_id in ("urt", "atmos", "nexo", "praxis"):
    marker = f"{component_id}: {{"
    if marker not in public_js:
        raise SystemExit(
            f"FAIL: public ecosystem component absent: {component_id}"
        )

if 'class="sister-core-card" href="/login"' not in index_html:
    raise SystemExit(
        "FAIL: SisTer core login boundary was unexpectedly removed"
    )

print("web public exploration boundary contract ok")
