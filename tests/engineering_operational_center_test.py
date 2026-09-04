#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_not_contains(text: str, forbidden: list[str], label: str) -> None:
    found = [term for term in forbidden if term in text]
    assert not found, f"{label} contem termos fora do nucleo operacional: {found}"


def main() -> None:
    index = read("web/engineering/index.html")
    app = read("web/engineering/app.js")
    styles = read("web/engineering/styles.css")
    home = read("web/index.html")
    home_app = read("web/app.js")
    public_app = read("web/public.js")
    main_cpp = read("apps/sisterd/main.cpp")
    db_hpp = read("apps/sisterd/db.hpp")
    db_cpp = read("apps/sisterd/db.cpp")
    migration = read("storage/migrations/013_integration_decisions.sql")
    local_resources = read("config/local_resources.json")
    starter = read("scripts/iniciar-sister.sh")

    forbidden = ["PDE", "Kanban", "Sprint", "Backlog", "Pull Request"]
    assert_not_contains(index, forbidden, "Centro de Engenharia")
    assert_not_contains(app, ["/api/v1/engineering/plan", "renderBoard", "renderCatalog"], "app.js")
    assert_not_contains(styles, ["board-section", "catalog-section"], "styles.css")

    assert "/api/v1/engineering/integrations/" in main_cpp
    assert "engineering.integration.decide" in main_cpp
    assert "engineering.integration.execute" in main_cpp
    assert "approved_integration_execution" in main_cpp
    assert "engineering.operational-base.read" in main_cpp
    assert "engineering.ecosystem.read" in main_cpp
    assert 'request.path.starts_with("/engineering/")' in main_cpp
    assert "/api/ecosystem" in app
    assert "Ecossistema implantado" in index
    assert "/api/v1/workspace" in home_app
    assert "/api/ecosystem" not in home_app
    assert "/api/contracts" not in home_app
    assert "/api/evidence" not in home_app
    assert "/api/diagnostics" not in home_app
    assert "Leitura territorial" not in home
    assert "Mapa territorial sintético" not in home
    assert "Recursos disponíveis" in home
    assert 'fetch("/api/me"' in public_app
    assert 'response.status === 401' in public_app
    assert "window.__sisterUser" in public_app
    for participant_id in ("nexo", "praxis", "urt", "atmos"):
        assert participant_id not in home_app.lower()
    assert "no-store, no-cache, must-revalidate, max-age=0" in main_cpp
    assert "Clear-Site-Data" in main_cpp
    assert "decideIntegration" in db_hpp
    assert "integrationApproved" in db_hpp
    assert "recordIntegrationExecution" in db_hpp
    assert "sister_integration_decisions" in db_cpp
    assert "CREATE TABLE IF NOT EXISTS sister_integration_decisions" in migration
    assert "decision IN ('approved', 'rejected')" in migration
    assert_not_contains(
        local_resources + starter,
        ["sister_nexo", "sister_compras", "sister_clima", "sister_campo", "8015", "8016", "8501"],
        "registro operacional local",
    )

    print("[OK] Centro de Engenharia restrito ao ciclo operacional do SisTer")


if __name__ == "__main__":
    main()
