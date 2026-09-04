#pragma once

#include <filesystem>
#include <string>
#include <string_view>
#include <vector>

namespace sister::ecosystem {

struct SemanticCapability {
    std::string capabilityId;
    std::string label;
    std::string authorityScope;
};

struct SemanticParticipant {
    std::string participantId;
    std::string label;
    std::string declaredState;
    std::string authorityScope;
    std::string provenanceRef;
    std::vector<SemanticCapability> capabilities;
};

struct SemanticView {
    std::string sourceStatus = "not_configured";
    std::string sourceRevision;
    std::vector<SemanticParticipant> participants;
};

// Parses a compact projection produced by an authoritative source. Invalid or
// absent input fails closed to an explicit empty view.
SemanticView parseSemanticProjection(std::string_view content);
SemanticView parseSemanticProjectionFile(const std::filesystem::path& path);

// Relations remain explicitly unavailable until a runtime-normative source exists.
std::string serializeSemanticViewJson(const SemanticView& view);

} // namespace sister::ecosystem
