#include "sister/contract.hpp"
#include "sister/provenance.hpp"
#include "sister/registry.hpp"

#include <cstdlib>
#include <iostream>
#include <string>

namespace {

void expect(bool condition, const std::string& message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

sister::SystemManifest validManifest() {
    sister::SystemManifest manifest;
    manifest.system_id = "morfocampo";
    manifest.system_name = "MorfoCampo";
    manifest.system_version = "0.2.1";
    manifest.contract_version = "sister-contracts/0.1.0";
    manifest.type = "field_system";
    manifest.domain = {"campo_nativo", "observacao_campo"};
    manifest.operational_mode = {"offline", "local_network"};
    manifest.exports = {"observations", "evidence", "spatial_context"};
    manifest.integration_modes = {"camposync_package", "local_api"};
    manifest.responsible_repository = "morfocampo";
    manifest.data_policy.requires_provenance = true;
    manifest.data_policy.allows_offline_sync = true;
    manifest.data_policy.requires_schema_validation = true;
    return manifest;
}

} // namespace

int main() {
    auto manifest = validManifest();
    expect(sister::validateSystemManifest(manifest).ok, "valid manifest should pass");

    manifest.data_policy.requires_provenance = false;
    expect(!sister::validateSystemManifest(manifest).ok, "manifest without provenance should fail");

    sister::SystemRegistry registry;
    expect(registry.registerSystem(validManifest()).ok, "registry should accept valid system");
    expect(registry.findById("morfocampo").has_value(), "registry should find registered system");

    const sister::ProvenanceRecord provenance{
        "obs-001",
        "morfocampo",
        "sister-contracts/0.1.0",
        "evidence/photos/obs-001.jpg",
        "2026-07-09T21:30:00-03:00"
    };
    expect(sister::hasMinimumProvenance(provenance), "minimum provenance should pass");

    std::cout << "sister_core_tests ok\n";
    return 0;
}
