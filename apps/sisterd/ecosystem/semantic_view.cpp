#include "ecosystem/semantic_view.hpp"

#include "ecosystem/ecosystem_view.hpp"

#include <algorithm>
#include <fstream>
#include <iterator>

namespace sister::ecosystem {

namespace {

constexpr std::size_t kMaxSemanticProjectionBytes = 1024 * 1024;

std::vector<std::string_view> splitByTab(std::string_view line) {
    std::vector<std::string_view> tokens;
    std::size_t start = 0;
    while (start <= line.size()) {
        const auto tab = line.find('\t', start);
        if (tab == std::string_view::npos) {
            tokens.push_back(line.substr(start));
            break;
        }
        tokens.push_back(line.substr(start, tab - start));
        start = tab + 1;
    }
    return tokens;
}

bool validText(std::string_view value) {
    return !value.empty() && value.find_first_of("\r\n\t") == std::string_view::npos;
}

} // namespace

SemanticView parseSemanticProjection(std::string_view content) {
    SemanticView view;
    bool authoritativeHeader = false;
    std::size_t lineStart = 0;

    while (lineStart < content.size()) {
        auto lineEnd = content.find('\n', lineStart);
        if (lineEnd == std::string_view::npos) lineEnd = content.size();
        auto line = content.substr(lineStart, lineEnd - lineStart);
        lineStart = lineEnd + 1;
        if (!line.empty() && line.back() == '\r') line.remove_suffix(1);
        if (line.empty() || line.front() == '#') continue;

        const auto tokens = splitByTab(line);
        if (tokens[0] == "META") {
            authoritativeHeader = tokens.size() >= 3 &&
                tokens[1] == "sister.semantic-ecosystem-source/1.0.0" &&
                validText(tokens[2]);
            if (authoritativeHeader) view.sourceRevision = std::string(tokens[2]);
            continue;
        }
        if (!authoritativeHeader) continue;

        if (tokens[0] == "PARTICIPANT" && tokens.size() >= 6 &&
            validText(tokens[1]) && validText(tokens[2]) && validText(tokens[3]) &&
            validText(tokens[4]) && validText(tokens[5])) {
            const auto duplicate = std::find_if(
                view.participants.begin(), view.participants.end(),
                [&](const SemanticParticipant& item) { return item.participantId == tokens[1]; });
            if (duplicate == view.participants.end()) {
                view.participants.push_back({
                    std::string(tokens[1]), std::string(tokens[2]), std::string(tokens[3]),
                    std::string(tokens[4]), std::string(tokens[5]), {}});
            }
        } else if (tokens[0] == "CAPABILITY" && tokens.size() >= 5 &&
                   validText(tokens[1]) && validText(tokens[2]) &&
                   validText(tokens[3]) && validText(tokens[4])) {
            const auto participant = std::find_if(
                view.participants.begin(), view.participants.end(),
                [&](const SemanticParticipant& item) { return item.participantId == tokens[1]; });
            if (participant != view.participants.end()) {
                participant->capabilities.push_back({
                    std::string(tokens[2]), std::string(tokens[3]), std::string(tokens[4])});
            }
        }
    }

    if (!authoritativeHeader) {
        view = {};
        view.sourceStatus = "invalid";
        return view;
    }
    view.sourceStatus = "authoritative";
    return view;
}

SemanticView parseSemanticProjectionFile(const std::filesystem::path& path) {
    if (path.empty()) return {};
    std::error_code error;
    const auto size = std::filesystem::file_size(path, error);
    if (error) {
        SemanticView view;
        view.sourceStatus = "unavailable";
        return view;
    }
    if (size > kMaxSemanticProjectionBytes) {
        SemanticView view;
        view.sourceStatus = "invalid";
        return view;
    }
    std::ifstream input(path);
    if (!input) {
        SemanticView view;
        view.sourceStatus = "unavailable";
        return view;
    }
    const std::string content{
        std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
    return parseSemanticProjection(content);
}

std::string serializeSemanticViewJson(const SemanticView& view) {
    std::string json = "{\n  \"schema\": \"sister.semantic-ecosystem-view/1.0.0\",\n";
    json += "  \"source_status\": \"" + jsonEscape(view.sourceStatus) + "\",\n";
    json += "  \"source_revision\": \"" + jsonEscape(view.sourceRevision) + "\",\n";
    json += "  \"participants\": [";
    for (std::size_t index = 0; index < view.participants.size(); ++index) {
        const auto& participant = view.participants[index];
        if (index > 0) json += ',';
        json += "\n    {\n";
        json += "      \"participant_id\": \"" + jsonEscape(participant.participantId) + "\",\n";
        json += "      \"label\": \"" + jsonEscape(participant.label) + "\",\n";
        json += "      \"declared_state\": \"" + jsonEscape(participant.declaredState) + "\",\n";
        json += "      \"authority_scope\": \"" + jsonEscape(participant.authorityScope) + "\",\n";
        json += "      \"provenance_ref\": \"" + jsonEscape(participant.provenanceRef) + "\",\n";
        json += "      \"capabilities\": [";
        for (std::size_t capabilityIndex = 0;
             capabilityIndex < participant.capabilities.size(); ++capabilityIndex) {
            const auto& capability = participant.capabilities[capabilityIndex];
            if (capabilityIndex > 0) json += ',';
            json += "\n        {\"capability_id\": \"" + jsonEscape(capability.capabilityId) +
                "\", \"label\": \"" + jsonEscape(capability.label) +
                "\", \"authority_scope\": \"" + jsonEscape(capability.authorityScope) + "\"}";
        }
        if (!participant.capabilities.empty()) json += "\n      ";
        json += "]\n    }";
    }
    if (!view.participants.empty()) json += "\n  ";
    json += "],\n  \"relations\": [],\n  \"relations_status\": \"not_available\"\n}";
    return json;
}

} // namespace sister::ecosystem
