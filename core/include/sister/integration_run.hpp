#pragma once

#include <cstdint>
#include <string>
#include <optional>
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

struct TransitionError final {
    std::string transition;
    std::string message;
};

struct RetryRelation final { RunId parent; };
struct ReprocessRelation final { RunId source; };
struct SupersessionRelation final { RunId successor; std::string reason; };
using RunRelation = std::variant<RetryRelation, ReprocessRelation, SupersessionRelation>;

enum class ExecutionStatus { proposed, authorized, running, completed, failed, cancelled, superseded };
enum class ValidityStatus { pending, valid, invalid, superseded };

enum class ExecutionTransition { authorize, start, complete, fail, cancel, supersede };
enum class ValidityTransition { mark_valid, mark_invalid, supersede };

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

struct ExecutionTransitionContext final {
    std::string at;
    std::vector<ArtifactReference> outputs;
    ExecutionError error;
    std::optional<RunId> successor;
    std::string reason;
    std::string cancellation_reason;
};

struct ValidityTransitionContext final {
    std::string at;
    std::optional<RunId> successor;
    std::string reason;
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
    [[nodiscard]] const std::vector<ArtifactReference>& outputs() const noexcept { return outputs_; }
    [[nodiscard]] const std::vector<RunRelation>& relations() const noexcept { return relations_; }
    [[nodiscard]] const std::vector<ExecutionError>& errors() const noexcept { return errors_; }
    [[nodiscard]] const std::string& startedAt() const noexcept { return started_at_; }
    [[nodiscard]] const std::string& authorizedAt() const noexcept { return authorized_at_; }
    [[nodiscard]] const std::string& finishedAt() const noexcept { return finished_at_; }
    [[nodiscard]] const std::string& cancellationReason() const noexcept { return cancellation_reason_; }

private:
    friend std::variant<IntegrationRun, DomainError>
    proposeIntegrationRun(IntegrationRunProposal proposal);
    friend std::variant<IntegrationRun, TransitionError>
    transitionExecution(IntegrationRun current, ExecutionTransition transition,
                        const ExecutionTransitionContext& context);
    friend std::variant<IntegrationRun, TransitionError>
    transitionValidity(IntegrationRun current, ValidityTransition transition,
                       const ValidityTransitionContext& context);

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
    std::vector<ArtifactReference> outputs_;
    std::vector<EvidenceReference> evidence_;
    std::vector<ExecutionError> errors_;
    std::vector<RunRelation> relations_;
    std::string authorized_at_;
    std::string started_at_;
    std::string finished_at_;
    std::string cancellation_reason_;
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

inline std::variant<IntegrationRun, TransitionError>
transitionExecution(IntegrationRun current, ExecutionTransition transition,
                    const ExecutionTransitionContext& context) {
    const auto reject = [&](const char* message) -> std::variant<IntegrationRun, TransitionError> {
        return TransitionError{"execution", message};
    };
    if (context.at.empty()) return reject("transition timestamp is required");

    switch (transition) {
    case ExecutionTransition::authorize:
        if (current.execution_status_ != ExecutionStatus::proposed) return reject("only proposed runs can be authorized");
        current.execution_status_ = ExecutionStatus::authorized;
        current.authorized_at_ = context.at;
        return current;
    case ExecutionTransition::start:
        if (current.execution_status_ != ExecutionStatus::authorized) return reject("only authorized runs can start");
        current.execution_status_ = ExecutionStatus::running;
        current.started_at_ = context.at;
        return current;
    case ExecutionTransition::complete:
        if (current.execution_status_ != ExecutionStatus::running) return reject("only running runs can complete");
        if (context.outputs.empty()) return reject("completed runs require output");
        current.execution_status_ = ExecutionStatus::completed;
        current.outputs_ = context.outputs;
        current.finished_at_ = context.at;
        return current;
    case ExecutionTransition::fail:
        if (current.execution_status_ != ExecutionStatus::running) return reject("only running runs can fail");
        if (context.error.code.empty() || context.error.message.empty()) return reject("failed runs require an error");
        current.execution_status_ = ExecutionStatus::failed;
        current.errors_.push_back(context.error);
        current.finished_at_ = context.at;
        return current;
    case ExecutionTransition::cancel:
        if (current.execution_status_ != ExecutionStatus::running) return reject("only running runs can be cancelled");
        if (context.cancellation_reason.empty()) return reject("cancelled runs require a reason");
        current.execution_status_ = ExecutionStatus::cancelled;
        current.cancellation_reason_ = context.cancellation_reason;
        current.finished_at_ = context.at;
        return current;
    case ExecutionTransition::supersede:
        if (current.execution_status_ != ExecutionStatus::completed && current.execution_status_ != ExecutionStatus::failed && current.execution_status_ != ExecutionStatus::cancelled) return reject("only terminal runs can be superseded");
        if (!context.successor.has_value() || context.reason.empty()) return reject("supersession requires successor and reason");
        current.execution_status_ = ExecutionStatus::superseded;
        current.validity_status_ = ValidityStatus::superseded;
        current.relations_.push_back(SupersessionRelation{*context.successor, context.reason});
        return current;
    }
    return reject("unknown execution transition");
}

inline std::variant<IntegrationRun, TransitionError>
transitionValidity(IntegrationRun current, ValidityTransition transition,
                   const ValidityTransitionContext& context) {
    if (context.at.empty()) return TransitionError{"validity", "transition timestamp is required"};
    if (current.execution_status_ == ExecutionStatus::superseded) return TransitionError{"validity", "superseded runs cannot change validity"};
    switch (transition) {
    case ValidityTransition::mark_valid:
        if (current.execution_status_ != ExecutionStatus::completed) return TransitionError{"validity", "only completed runs can become valid"};
        if (current.validity_status_ != ValidityStatus::pending) return TransitionError{"validity", "only pending runs can become valid"};
        current.validity_status_ = ValidityStatus::valid;
        return current;
    case ValidityTransition::mark_invalid:
        if (current.execution_status_ != ExecutionStatus::completed) return TransitionError{"validity", "only completed runs can become invalid"};
        if (current.validity_status_ != ValidityStatus::pending) return TransitionError{"validity", "only pending runs can become invalid"};
        current.validity_status_ = ValidityStatus::invalid;
        return current;
    case ValidityTransition::supersede:
        if (!context.successor.has_value() || context.reason.empty()) return TransitionError{"validity", "supersession requires successor and reason"};
        current.validity_status_ = ValidityStatus::superseded;
        current.relations_.push_back(SupersessionRelation{*context.successor, context.reason});
        return current;
    }
    return TransitionError{"validity", "unknown validity transition"};
}

} // namespace sister
