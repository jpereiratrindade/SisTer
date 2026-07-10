#pragma once

#include <string>

namespace sister {

struct ProvenanceRecord {
    std::string object_id;
    std::string source_system_id;
    std::string contract_version;
    std::string evidence_ref;
    std::string observed_at;
};

bool hasMinimumProvenance(const ProvenanceRecord& record);

} // namespace sister
