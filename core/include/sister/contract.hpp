#pragma once

#include <map>
#include <string>
#include <string_view>
#include <vector>

namespace sister {

struct DataPolicy {
    bool requires_provenance = false;
    bool allows_offline_sync = false;
    bool requires_schema_validation = false;
    bool requires_operator = false;
    bool requires_spatial_reference = false;
};

struct SystemManifest {
    std::string system_id;
    std::string system_name;
    std::string system_version;
    std::string contract_version;
    std::string type;
    std::vector<std::string> domain;
    std::vector<std::string> operational_mode;
    std::vector<std::string> exports;
    std::vector<std::string> integration_modes;
    std::string responsible_repository;
    DataPolicy data_policy;
};

struct ValidationIssue {
    std::string field;
    std::string message;
};

struct ValidationResult {
    bool ok = false;
    std::vector<ValidationIssue> issues;
};

ValidationResult validateSystemManifest(const SystemManifest& manifest);
SystemManifest parseSystemManifestJson(std::string_view json);
std::string to_string(const ValidationResult& result);

} // namespace sister
