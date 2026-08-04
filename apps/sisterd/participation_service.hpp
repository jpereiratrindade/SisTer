#pragma once

#include "db.hpp"

#include <string>
#include <variant>

namespace sisterd {

struct AuthenticatedPrincipal {
    std::string subject;
    std::string authenticationSource;
};

struct ParticipationServiceError {
    int status;
    std::string code;
    std::string detail;
};

class ParticipationService {
public:
    explicit ParticipationService(DbConn& db) : db_(db) {}

    std::variant<std::string, ParticipationServiceError> propose(
        const AuthenticatedPrincipal* principal,
        std::string contractJson,
        std::string participationId,
        std::string participantSystemId,
        std::string contractVersion,
        std::string contractDigest,
        std::string sourceCommit);
    std::variant<std::string, ParticipationServiceError> show(const std::string& participationId);
    std::variant<std::string, ParticipationServiceError> recordTechnicalAssessment(
        const std::string& assessmentId, const std::string& participationId,
        const std::string& contractDigest, const std::string& evaluatedCommit,
        const std::string& assessmentJson);

private:
    DbConn& db_;
};

} // namespace sisterd
