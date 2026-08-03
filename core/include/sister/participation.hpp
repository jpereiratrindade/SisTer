#pragma once

#include <algorithm>
#include <compare>
#include <string>
#include <utility>
#include <variant>
#include <vector>

namespace sister::participation {

template <typename Tag>
class ParticipationIdentifier final {
public:
    explicit ParticipationIdentifier(std::string value) : value_(std::move(value)) {}
    [[nodiscard]] const std::string& value() const noexcept { return value_; }
    auto operator<=>(const ParticipationIdentifier&) const = default;

private:
    std::string value_;
};

struct ParticipationIdTag;
struct CapabilityIdTag;
struct ContributionTypeIdTag;
struct AssessmentIdTag;
struct EvidenceIdTag;

using ParticipationId = ParticipationIdentifier<ParticipationIdTag>;
using CapabilityId = ParticipationIdentifier<CapabilityIdTag>;
using ContributionTypeId = ParticipationIdentifier<ContributionTypeIdTag>;
using AssessmentId = ParticipationIdentifier<AssessmentIdTag>;
using EvidenceId = ParticipationIdentifier<EvidenceIdTag>;

enum class ParticipationState { proposed, assessed, authorized, suspended, revoked };

struct CapabilityDefinition final {
    CapabilityId id;
    std::string purpose;
    std::string inputSchema;
    std::string outputSchema;
    std::vector<std::string> preconditions;
    std::vector<std::string> risks;
    std::string responsibleRole;
    std::string reflexivityProfile;
};

struct ContributionDefinition final {
    ContributionTypeId typeId;
    std::string purpose;
    std::string validityPolicy;
    std::string uncertaintyPolicy;
    std::vector<std::string> restrictions;
};

struct AuthorityAllocation final {
    std::string originAuthority;
    std::string productionAuthority;
    std::string custodyAuthority;
    std::string interpretationAuthority;
    std::string decisionAuthority;
    std::string consumptionAuthority;
};

struct BoundaryObjectEnvelope final {
    std::string envelopeId;
    std::string objectType;
    std::string correlationId;
    ParticipationId participationId;
    std::string contractVersion;
    std::string authorityReference;
    std::string integrityDigest;
    std::string context;
    std::vector<EvidenceId> provenance;
    std::string payload;
};

enum class AssessmentResult { pass, warn, shadow, block, inconclusive };
enum class AssessmentLayer { existence, contribution, interaction, governance, reflection };

struct AssessmentFinding final {
    std::string code;
    AssessmentLayer layer;
    std::string explanation;
    std::vector<EvidenceId> evidence;
};

struct ParticipationAssessment final {
    AssessmentId id;
    ParticipationId participationId;
    std::string contractVersion;
    std::string contractDigest;
    std::string evaluatedCommit;
    std::string profileId;
    std::string evaluatorId;
    std::string evaluatorVersion;
    AssessmentResult result;
    std::vector<AssessmentFinding> findings;
    std::vector<EvidenceId> evidenceUsed;
    std::vector<std::string> evidenceMissing;
    double confidence;
    std::vector<std::string> limitations;
    std::string gateEffect;
    std::string recommendation;
    std::string assessedAt;
};

struct ParticipationContractDraft final {
    ParticipationId id;
    std::string participantSystemId;
    std::string purpose;
    std::string owner;
    std::string entryConditions;
    std::string suspensionConditions;
    std::string exitConditions;
    std::vector<CapabilityDefinition> capabilities;
    std::vector<ContributionDefinition> contributions;
    AuthorityAllocation authority;
};

struct ParticipationDomainError final {
    std::string code;
    std::string message;
};

class ParticipationContract final {
public:
    [[nodiscard]] const ParticipationId& id() const noexcept { return draft_.id; }
    [[nodiscard]] const std::string& participantSystemId() const noexcept {
        return draft_.participantSystemId;
    }
    [[nodiscard]] ParticipationState state() const noexcept { return state_; }
    [[nodiscard]] const std::vector<CapabilityDefinition>& capabilities() const noexcept {
        return draft_.capabilities;
    }
    [[nodiscard]] const std::vector<ContributionDefinition>& contributions() const noexcept {
        return draft_.contributions;
    }
    [[nodiscard]] const AuthorityAllocation& authority() const noexcept { return draft_.authority; }

private:
    friend std::variant<ParticipationContract, ParticipationDomainError>
    proposeParticipation(ParticipationContractDraft draft);

    explicit ParticipationContract(ParticipationContractDraft draft)
        : draft_(std::move(draft)) {}

    ParticipationContractDraft draft_;
    ParticipationState state_{ParticipationState::proposed};
};

inline std::variant<ParticipationContract, ParticipationDomainError>
proposeParticipation(ParticipationContractDraft draft) {
    const auto missing = [](const std::string& value) { return value.empty(); };
    if (missing(draft.id.value()) || missing(draft.participantSystemId) ||
        missing(draft.purpose) || missing(draft.owner) || missing(draft.entryConditions) ||
        missing(draft.suspensionConditions) || missing(draft.exitConditions)) {
        return ParticipationDomainError{"participation.required_field", "required field is empty"};
    }
    if (draft.capabilities.empty() || draft.contributions.empty()) {
        return ParticipationDomainError{"participation.empty_offer", "capability and contribution are required"};
    }
    std::vector<std::string> capabilityIds;
    for (const auto& capability : draft.capabilities) {
        if (missing(capability.id.value()) || missing(capability.purpose) ||
            missing(capability.inputSchema) || missing(capability.outputSchema) ||
            missing(capability.responsibleRole) || capability.reflexivityProfile != "D2/A1/shadow") {
            return ParticipationDomainError{"participation.invalid_capability", "capability is incomplete"};
        }
        capabilityIds.push_back(capability.id.value());
    }
    std::ranges::sort(capabilityIds);
    if (std::adjacent_find(capabilityIds.begin(), capabilityIds.end()) != capabilityIds.end()) {
        return ParticipationDomainError{"participation.duplicate_capability", "capability id is duplicated"};
    }
    const auto& authority = draft.authority;
    if (missing(authority.originAuthority) || missing(authority.productionAuthority) ||
        missing(authority.custodyAuthority) || missing(authority.interpretationAuthority) ||
        missing(authority.decisionAuthority) || missing(authority.consumptionAuthority)) {
        return ParticipationDomainError{"participation.incomplete_authority", "authority allocation is incomplete"};
    }
    return ParticipationContract{std::move(draft)};
}

}  // namespace sister::participation
