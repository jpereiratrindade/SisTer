#include "sister/contract.hpp"
#include "sister/provenance.hpp"
#include "sister/registry.hpp"
#include "sister/integration_run.hpp"

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

    auto makeId = [](auto tag, const char* value) {
        using Tag = decltype(tag);
        return std::get<sister::Identifier<Tag>>(sister::Identifier<Tag>::fromString(value));
    };
    sister::IntegrationRunProposal proposal{
        makeId(sister::RunIdTag{}, "RUN-001"),
        makeId(sister::AgreementIdTag{}, "AGR-001"),
        makeId(sister::IdempotencyKeyTag{}, "KEY-001"),
        makeId(sister::CorrelationIdTag{}, "COR-001"),
        {"nexo", "nexo-compras"},
        "integrar compra ao projeto",
        "nexo-compras.integration",
        {{makeId(sister::SchemaIdTag{}, "input/1.0.0"), makeId(sister::DigestTag{}, "sha256:input"), "input-001"}},
        {}
    };
    auto runResult = sister::proposeIntegrationRun(std::move(proposal));
    expect(std::holds_alternative<sister::IntegrationRun>(runResult), "valid run proposal should pass");
    const auto& run = std::get<sister::IntegrationRun>(runResult);
    expect(run.executionStatus() == sister::ExecutionStatus::proposed, "new run should be proposed");
    expect(run.validityStatus() == sister::ValidityStatus::pending, "new run validity should be pending");
    expect(run.inputs().size() == 1, "run should preserve input references");

    auto invalid = sister::IntegrationRunProposal{
        makeId(sister::RunIdTag{}, "RUN-002"), makeId(sister::AgreementIdTag{}, "AGR-001"),
        makeId(sister::IdempotencyKeyTag{}, "KEY-002"), makeId(sister::CorrelationIdTag{}, "COR-002"),
        {"nexo"}, "", "", {}, {}
    };
    expect(std::holds_alternative<sister::DomainError>(sister::proposeIntegrationRun(std::move(invalid))),
        "invalid run proposal should be rejected");

    auto authorize = sister::transitionExecution(std::get<sister::IntegrationRun>(runResult),
        sister::ExecutionTransition::authorize, {"2026-08-02T12:00:01Z", {}, {}, {}, "", ""});
    expect(std::holds_alternative<sister::IntegrationRun>(authorize), "proposed run should authorize");
    auto start = sister::transitionExecution(std::get<sister::IntegrationRun>(authorize),
        sister::ExecutionTransition::start, {"2026-08-02T12:00:02Z", {}, {}, {}, "", ""});
    expect(std::holds_alternative<sister::IntegrationRun>(start), "authorized run should start");
    auto completed = sister::transitionExecution(std::get<sister::IntegrationRun>(start),
        sister::ExecutionTransition::complete,
        {"2026-08-02T12:00:03Z", {{makeId(sister::SchemaIdTag{}, "output/1.0.0"), makeId(sister::DigestTag{}, "sha256:output"), "output-001"}}, {}, {}, "", ""});
    expect(std::holds_alternative<sister::IntegrationRun>(completed), "running run with output should complete");
    const auto& completedRun = std::get<sister::IntegrationRun>(completed);
    expect(completedRun.executionStatus() == sister::ExecutionStatus::completed, "run should be completed");
    expect(completedRun.validityStatus() == sister::ValidityStatus::pending, "completion must not decide validity");
    expect(!completedRun.authorizedAt().empty(), "authorization timestamp should be retained");
    expect(!completedRun.startedAt().empty(), "start timestamp should be retained");
    expect(!completedRun.finishedAt().empty(), "finish timestamp should be retained");

    auto valid = sister::transitionValidity(completedRun, sister::ValidityTransition::mark_valid,
        {"2026-08-02T12:00:04Z", {}, ""});
    expect(std::holds_alternative<sister::IntegrationRun>(valid), "pending run should become valid");

    auto invalidComplete = sister::transitionExecution(std::get<sister::IntegrationRun>(start),
        sister::ExecutionTransition::complete, {"2026-08-02T12:00:03Z", {}, {}, {}, "", ""});
    expect(std::holds_alternative<sister::TransitionError>(invalidComplete), "completion without output should fail");

    auto invalidStart = sister::transitionExecution(run, sister::ExecutionTransition::start,
        {"2026-08-02T12:00:02Z", {}, {}, {}, "", ""});
    expect(std::holds_alternative<sister::TransitionError>(invalidStart), "proposed run cannot start directly");
    expect(run.executionStatus() == sister::ExecutionStatus::proposed, "rejected transition must not mutate source");

    auto failed = sister::transitionExecution(std::get<sister::IntegrationRun>(start),
        sister::ExecutionTransition::fail, {"2026-08-02T12:00:05Z", {}, {"UPSTREAM", "unavailable"}, {}, "", ""});
    expect(std::holds_alternative<sister::IntegrationRun>(failed), "running run with error should fail");
    expect(std::get<sister::IntegrationRun>(failed).executionStatus() == sister::ExecutionStatus::failed, "run should be failed");

    auto cancelled = sister::transitionExecution(std::get<sister::IntegrationRun>(start),
        sister::ExecutionTransition::cancel, {"2026-08-02T12:00:06Z", {}, {}, {}, "operator request", "operator request"});
    expect(std::holds_alternative<sister::IntegrationRun>(cancelled), "running run with reason should cancel");
    expect(std::get<sister::IntegrationRun>(cancelled).cancellationReason() == "operator request", "cancel reason should be retained");

    auto superseded = sister::transitionExecution(completedRun, sister::ExecutionTransition::supersede,
        {"2026-08-02T12:00:07Z", {}, {}, makeId(sister::RunIdTag{}, "RUN-NEW"), "reprocess"});
    expect(std::holds_alternative<sister::IntegrationRun>(superseded), "terminal run should be supersedable");
    expect(std::get<sister::IntegrationRun>(superseded).executionStatus() == sister::ExecutionStatus::superseded, "run should be superseded");

    auto runningValid = sister::transitionValidity(std::get<sister::IntegrationRun>(start),
        sister::ValidityTransition::mark_valid, {"2026-08-02T12:00:08Z", {}, ""});
    expect(std::holds_alternative<sister::TransitionError>(runningValid), "running run cannot be marked valid");

    std::cout << "sister_core_tests ok\n";
    return 0;
}
