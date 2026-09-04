#pragma once

#include <cstdint>
#include <filesystem>
#include <string>
#include <string_view>
#include <vector>

namespace sister::ecosystem {

struct RuntimeBinding {
    std::string transport;
    std::string listen;
    uint16_t port = 0;
};

struct Probe {
    std::string healthPath;
};

struct GatewayPublication {
    std::string host;
    std::string publicUrl;
};

struct HealthObservation {
    std::string status = "not_observed"; // "online", "offline", "not_observed"
    int httpStatus = 0;
    std::string detail = "not_observed";
};

struct InteractionSurface {
    std::string surfaceId;
    std::string label;
    std::string purpose;
    std::string publicUrl;
    std::string accessClass;
};

struct EcosystemParticipant {
    std::string componentId;
    std::string systemId;
    RuntimeBinding runtime;
    Probe probe;
    GatewayPublication gateway;
    HealthObservation health;
    std::vector<InteractionSurface> interactionSurfaces;
};

struct EcosystemView {
    std::string schema = "sister.runtime.ecosystem-view/1";
    std::string compositionId;
    std::string deploymentId;
    std::string deploymentStatus = "NOT_CONFIGURED";
    std::vector<EcosystemParticipant> systems;
};

// Escapes a string for valid JSON output
std::string jsonEscape(std::string_view value);

// Parses projection TSV file into EcosystemView
EcosystemView parseProjectionFile(const std::filesystem::path& path);

// Parses projection TSV text directly
EcosystemView parseProjection(std::string_view content);

// Observes health for a single loopback HTTP endpoint
HealthObservation observeLoopbackHealth(
    uint16_t port,
    std::string_view path,
    int timeoutMilliseconds) noexcept;

// Observes health for all participants in the ecosystem view
void observeEcosystemHealth(EcosystemView& view, int timeoutMilliseconds) noexcept;

// Serializes EcosystemView to JSON (/api/ecosystem)
std::string serializeEcosystemViewJson(const EcosystemView& view);

// Serializes EcosystemView systems to JSON (/api/systems compatibility)
std::string serializeSystemsCompatibilityJson(const EcosystemView& view);

// Serializes only complete, navigable surfaces authorized for the actor.
std::string serializeWorkspaceViewJson(
    const EcosystemView& view,
    const std::vector<std::string_view>& allowedAccessClasses);

} // namespace sister::ecosystem
