#include "sister/contract.hpp"

#include <algorithm>
#include <cctype>
#include <regex>
#include <sstream>
#include <stdexcept>

namespace sister {
namespace {

bool blank(const std::string& value) {
    return std::all_of(value.begin(), value.end(), [](unsigned char c) {
        return std::isspace(c) != 0;
    });
}

void requireText(const std::string& field, const std::string& value, std::vector<ValidationIssue>& issues) {
    if (value.empty() || blank(value)) {
        issues.push_back({field, "required text field is empty"});
    }
}

void requireNonEmpty(const std::string& field, const std::vector<std::string>& values, std::vector<ValidationIssue>& issues) {
    if (values.empty()) {
        issues.push_back({field, "required list is empty"});
    }
}

std::string extractString(std::string_view json, const std::string& key) {
    const std::regex pattern("\"" + key + "\"\\s*:\\s*\"([^\"]*)\"");
    std::cmatch match;
    const std::string source(json);
    if (std::regex_search(source.c_str(), match, pattern)) {
        return match[1].str();
    }
    return {};
}

std::vector<std::string> extractStringArray(std::string_view json, const std::string& key) {
    const std::regex arrayPattern("\"" + key + "\"\\s*:\\s*\\[([^\\]]*)\\]");
    const std::regex itemPattern("\"([^\"]*)\"");
    std::cmatch arrayMatch;
    const std::string source(json);
    std::vector<std::string> values;

    if (!std::regex_search(source.c_str(), arrayMatch, arrayPattern)) {
        return values;
    }

    const std::string body = arrayMatch[1].str();
    for (std::sregex_iterator it(body.begin(), body.end(), itemPattern), end; it != end; ++it) {
        values.push_back((*it)[1].str());
    }
    return values;
}

bool extractBool(std::string_view json, const std::string& key) {
    const std::regex pattern("\"" + key + "\"\\s*:\\s*(true|false)");
    std::cmatch match;
    const std::string source(json);
    if (std::regex_search(source.c_str(), match, pattern)) {
        return match[1].str() == "true";
    }
    return false;
}

} // namespace

ValidationResult validateSystemManifest(const SystemManifest& manifest) {
    std::vector<ValidationIssue> issues;

    requireText("system_id", manifest.system_id, issues);
    requireText("system_name", manifest.system_name, issues);
    requireText("system_version", manifest.system_version, issues);
    requireText("contract_version", manifest.contract_version, issues);
    requireText("type", manifest.type, issues);
    requireNonEmpty("domain", manifest.domain, issues);
    requireNonEmpty("operational_mode", manifest.operational_mode, issues);
    requireNonEmpty("exports", manifest.exports, issues);
    requireNonEmpty("integration_modes", manifest.integration_modes, issues);

    if (!manifest.data_policy.requires_provenance) {
        issues.push_back({"data_policy.requires_provenance", "SisTer integration requires provenance"});
    }

    if (!manifest.data_policy.requires_schema_validation) {
        issues.push_back({"data_policy.requires_schema_validation", "contracted imports must require schema validation"});
    }

    return {issues.empty(), issues};
}

SystemManifest parseSystemManifestJson(std::string_view json) {
    SystemManifest manifest;
    manifest.system_id = extractString(json, "system_id");
    manifest.system_name = extractString(json, "system_name");
    manifest.system_version = extractString(json, "system_version");
    manifest.contract_version = extractString(json, "contract_version");
    manifest.type = extractString(json, "type");
    manifest.domain = extractStringArray(json, "domain");
    manifest.operational_mode = extractStringArray(json, "operational_mode");
    manifest.exports = extractStringArray(json, "exports");
    manifest.integration_modes = extractStringArray(json, "integration_modes");
    manifest.responsible_repository = extractString(json, "responsible_repository");
    manifest.data_policy.requires_provenance = extractBool(json, "requires_provenance");
    manifest.data_policy.allows_offline_sync = extractBool(json, "allows_offline_sync");
    manifest.data_policy.requires_schema_validation = extractBool(json, "requires_schema_validation");
    manifest.data_policy.requires_operator = extractBool(json, "requires_operator");
    manifest.data_policy.requires_spatial_reference = extractBool(json, "requires_spatial_reference");
    return manifest;
}

std::string to_string(const ValidationResult& result) {
    if (result.ok) {
        return "validation ok";
    }

    std::ostringstream out;
    out << "validation failed";
    for (const auto& issue : result.issues) {
        out << "\n- " << issue.field << ": " << issue.message;
    }
    return out.str();
}

} // namespace sister
