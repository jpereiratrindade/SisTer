#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "web/index.html").read_text(encoding="utf-8")
APP = (ROOT / "web/app.js").read_text(encoding="utf-8")
CSS = (ROOT / "web/home-experience.css").read_text(encoding="utf-8")

assert 'href="./home-experience.css"' in HTML
assert "Conhecimento integrado para territórios mais resilientes." in HTML
assert "Transformação de domínio" in HTML
assert "Transformação federativa" in HTML
assert "O participante transforma dados em conhecimento do seu domínio." in HTML
assert "O SisTer" in HTML and "contexto integrado de uso" in HTML

for role in (
    "Público / visitante",
    "Membro / colaborador",
    "Pesquisador",
    "Campo / técnico",
    "Especialista de domínio",
    "Coordenador científico",
    "Avaliador / governança",
    "Operador do ecossistema",
):
    assert role in HTML

assert 'id="workspace-resources"' in HTML
assert 'id="home-context-name"' in HTML
assert 'id="home-context-role"' in HTML
assert 'id="home-context-resources"' in HTML
assert 'data-open-view="ecosystem"' in HTML

# O primeiro corte usa somente contratos já existentes.
assert 'fetch("/api/v1/workspace"' in APP
assert 'fetch("/api/v1/ecosystem/semantic"' in APP
assert "/api/v1/home-experience" not in APP
assert "/api/v1/context" not in APP

# A Home autenticada não deve fabricar projeto, território ou observações científicas.
home = HTML[HTML.index('id="view-home"'):HTML.index('id="view-ecosystem"')]
for fabricated in ("83 mm", "URT Bagé", "setembro/2025", "3 novas evidências"):
    assert fabricated not in home

assert ".experience-transform-grid" in CSS
assert ".experience-audience-grid" in CSS
assert "prefers-reduced-motion" in CSS

print("web home experience contract test: ok")
