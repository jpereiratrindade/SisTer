#include "sister/provenance.hpp"

namespace sister {

bool hasMinimumProvenance(const ProvenanceRecord& record) {
    return !record.object_id.empty()
        && !record.source_system_id.empty()
        && !record.contract_version.empty()
        && !record.evidence_ref.empty()
        && !record.observed_at.empty();
}

} // namespace sister
