#!/usr/bin/env python3

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HTML = (ROOT / "web/index.html").read_text(encoding="utf-8")
CSS = (ROOT / "web/ecosystem-pixel-exact.css").read_text(encoding="utf-8")
PUBLIC = (ROOT / "web/public.js").read_text(encoding="utf-8")

assert 'href="./ecosystem-pixel-exact.css"' in HTML

assert 'viewBox="0 0 1672 941"' in HTML
assert 'preserveAspectRatio="xMidYMid meet"' in HTML

assert 'href="./assets/sister-experience-reference.png"' in HTML
assert 'width="1672"' in HTML
assert 'height="941"' in HTML

# The SisTer login boundary remains explicit.
assert 'class="sister-core-card"' in HTML
assert 'class="pixel-hotspot pixel-hotspot--sister"' in HTML
assert 'href="/login"' in HTML

# Public participants remain semantically addressable.
for component_id in ("urt", "atmos", "nexo", "praxis"):
    assert f'data-system="{component_id}"' in HTML
    assert f'href="/_sister/open/{component_id}"' in HTML

# Context stays independent from the pixels.
for context_id in (
    "person",
    "role",
    "project",
    "activity",
    "territory",
    "period",
):
    assert f'data-context="{context_id}"' in HTML

assert 'id="context-status-title"' in HTML
assert 'id="context-status-copy"' in HTML

# Runtime smoke invariants remain represented semantically even
# when their visual expression belongs to the raster reference.
for semantic_witness in (
    "Pessoa situada em um",
    "ambiente computacional",
    "contexto vem antes da capacidade",
    "Ecossistema federado e semântico",
):
    assert semantic_witness.lower() in HTML.lower()

# The old visual reconstruction is no longer the public rendering authority.
public_home = HTML[
    HTML.index('id="public-home"'):
    HTML.index('id="authenticated-workspace"')
]

assert 'class="system-card ' not in public_home
assert 'class="context-node ' not in public_home
assert 'class="ecosystem-orbit"' not in public_home

# No global JS scaling is allowed.
for forbidden in (
    "syncEcosystemViewport",
    "--ecosystem-scale",
    "--ecosystem-stage-width",
    "--ecosystem-stage-height",
):
    assert forbidden not in PUBLIC

# SVG anchors preserve native fallback URLs but JS owns the richer interaction.
assert "event.preventDefault();" in PUBLIC

# Full-viewport composition; no prototype toolbar is transported.
assert "height: 100dvh;" in CSS
assert "pixel-exact-scene" in CSS
assert "LAB visual isolado" not in HTML
assert "Mostrar hotspots" not in HTML
assert "Debug" not in HTML

print("web pixel-exact home contract: ok")
