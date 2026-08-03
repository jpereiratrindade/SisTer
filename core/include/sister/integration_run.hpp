#pragma once

#include <cstdint>
#include <string>
#include <utility>
#include <variant>
#include <vector>

namespace sister {

struct DomainError final {
    std::string field;
    std::string message;
};

template <typename Tag>
class Identifier final {
public:
    static std::variant<Identifier, DomainError> fromString(std::string value) {
        if (value.empty()) {
            return DomainError{"identifier", "value must not be empty"};
        }
        return Identifier{std::move(value)};
    }

    [[nodiscard]] const std::string& value() const noexcept { return value_; }
    friend bool operator==(const Identifier&, const Identifier&) = default;

private:
    explicit Identifier(std::string value) : value_(std::move(value)) {}
    std::string value_;
};

struct RunIdTag {};
struct AgreementIdTag {};
struct IdempotencyKeyTag {};
struct CorrelationIdTag {};
struct SchemaIdTag {};
struct DigestTag {};
struct EvidenceIdTag {};

using RunId = Identifier<RunIdTag>;
using AgreementId = Identifier<AgreementIdTag>;
using IdempotencyKey = Identifier<IdempotencyKeyTag>;
using CorrelationId = Identifier<CorrelationIdTag>;
using SchemaId = Identifier<SchemaIdTag>;
using Digest = Identifier<DigestTag>;
using EvidenceId = Identifier<EvidenceIdTag>;

struct ArtifactReference final {
    SchemaId schema;
    Digest digest;
    std::string reference_id;
};

struct EvidenceReference final {
    EvidenceId id;
    SchemaId schema;
    Digest digest;
    std::string location;
};

struct ExecutionError final {
    std::string code;
    std::string message;
};

struct RetryRelation final { RunId parent; };
struct ReprocessRelation final { RunId source; };
struct SupersessionRelation final { RunId successor; std::string reason; };
using RunRelation = std::variant<RetryRelation, ReprocessRelation, SupersessionRelation>;

enum class ExecutionStatus { proposed, authorized, running, completed, failed, cancelled, superseded };
enum class ValidityStatus { pending, valid, invalid, superseded };

struct IntegrationRunProposal final {
    RunId run_id;
    AgreementId agreement_id;
    IdempotencyKey idempotency_key;
    CorrelationId correlation_id;
    std::vector<std::string> participants;
    std::string purpose;
    std::string capability;
    std::vector<ArtifactReference> inputs;
    std::vector<EvidenceReference> evidence;
};

class IntegrationRun final {
public:
    [[nodiscard]] const RunId& id() const noexcept { return run_id_; }
    [[nodiscard]] const AgreementId& agreementId() const noexcept { return agreement_id_; }
    [[nodiscard]] const IdempotencyKey& idempotencyKey() const noexcept { return idempotency_key_; }
    [[nodiscard]] const CorrelationId& correlationId() const noexcept { return correlation_id_; }
    [[nodiscard]] ExecutionStatus executionStatus() const noexcept { return execution_status_; }
    [[nodiscard]] ValidityStatus validityStatus() const noexcept { return validity_status_; }
    [[nodiscard]] const std::vector<ArtifactReference>& inputs() const noexcept { return inputs_; }
    [[nodiscard]] const std::vector<EvidenceReference>& evidence() const noexcept { return evidence_; }

private:
    friend std::variant<IntegrationRun, DomainError>
    proposeIntegrationRun(IntegrationRunProposal proposal);

    explicit IntegrationRun(IntegrationRunProposal proposal)
        : run_id_(std::move(proposal.run_id)),
          agreement_id_(std::move(proposal.agreement_id)),
          idempotency_key_(std::move(proposal.idempotency_key)),
          correlation_id_(std::move(proposal.correlation_id)),
          execution_status_(ExecutionStatus::proposed),
          validity_status_(ValidityStatus::pending),
          inputs_(std::move(proposal.inputs)),
          evidence_(std::move(proposal.evidence)) {}

    RunId run_id_;
    AgreementId agreement_id_;
    IdempotencyKey idempotency_key_;
    CorrelationId correlation_id_;
    ExecutionStatus execution_status_;
    ValidityStatus validity_status_;
    std::vector<ArtifactReference> inputs_;
    std::vector<EvidenceReference> evidence_;
};

inline std::variant<IntegrationRun, DomainError>
proposeIntegrationRun(IntegrationRunProposal proposal) {
    if (proposal.participants.size() < 2) {
        return DomainError{"participants", "at least two participants are required"};
    }
    if (proposal.purpose.empty()) {
        return DomainError{"purpose", "purpose must not be empty"};
    }
    if (proposal.capability.empty()) {
        return DomainError{"capability", "capability must not be empty"};
    }
    if (proposal.inputs.empty()) {
        return DomainError{"inputs", "at least one input is required"};
    }
    return IntegrationRun{std::move(proposal)};
}

} // namespace sister
