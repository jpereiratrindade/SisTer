#!/usr/bin/env python3

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CSS = (ROOT / "web/home-experience.css").read_text(encoding="utf-8")
PUBLIC = (ROOT / "web/public.js").read_text(encoding="utf-8")
HTML = (ROOT / "web/index.html").read_text(encoding="utf-8")

# Public shell is a single viewport-owned workspace.
assert 'grid-template-areas: "workspace";' in CSS
assert "min-height: 100dvh;" in CSS
assert ".public-mode .workspace" in CSS
assert "min-height: 0;" in CSS

# No artificial desktop floor.
assert "min-height: max(100vh, 860px)" not in CSS

# Dynamic viewport, with natural scrolling when accessibility
# zoom or a short window makes the content intrinsically taller.
assert "overflow-x: hidden;" in CSS
assert "overflow-y: auto;" in CSS
assert "calc(100dvh - 78px)" in CSS

# The Home must not counteract browser zoom with JS scaling.
for forbidden in (
    "syncEcosystemViewport",
    "ECOSYSTEM_REFERENCE_HEIGHT",
    "ECOSYSTEM_VISUAL_SELECTORS",
):
    assert forbidden not in PUBLIC

for forbidden in (
    "--ecosystem-scale",
    "--ecosystem-stage-width",
    "--ecosystem-stage-height",
):
    assert forbidden not in PUBLIC
    assert forbidden not in CSS

assert 'class="ecosystem-stage"' not in HTML

print("web ecosystem viewport contract: ok")
