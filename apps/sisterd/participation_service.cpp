#include "participation_service.hpp"

namespace sisterd {

std::variant<std::string, ParticipationServiceError> ParticipationService::propose(
    const AuthenticatedPrincipal* principal, std::string contractJson, std::string participationId,
    std::string participantSystemId, std::string contractVersion, std::string contractDigest,
    std::string sourceCommit) {
    if (principal == nullptr) return ParticipationServiceError{401, "authentication_required", "Identidade autenticada necessária."};
    if (participationId.empty() || participantSystemId.empty() || contractVersion.empty() ||
        contractDigest.empty() || contractJson.empty()) {
        return ParticipationServiceError{400, "invalid_proposal", "A proposta está incompleta."};
    }
    if (participantSystemId != "sister_reference" || contractVersion != "1.0.0") {
        return ParticipationServiceError{400, "unsupported_contract", "Contrato de participação não suportado."};
    }
    if (contractJson.find("\"state\":\"proposed\"") == std::string::npos &&
        contractJson.find("\"state\": \"proposed\"") == std::string::npos) {
        return ParticipationServiceError{400, "invalid_state", "A proposta deve iniciar em proposed."};
    }
    DbConn::ParticipationProposal proposal{
        std::move(participationId), std::move(participantSystemId), std::move(contractVersion),
        std::move(contractDigest), std::move(contractJson), principal->subject,
        principal->authenticationSource, std::move(sourceCommit)};
    auto receipt = db_.registerParticipationProposal(proposal);
    if (!receipt) return ParticipationServiceError{503, "persistence_unavailable", "Persistência de participação indisponível."};
    return *receipt;
}

std::variant<std::string, ParticipationServiceError> ParticipationService::show(
    const std::string& participationId) {
    if (participationId.empty()) return ParticipationServiceError{404, "not_found", "Participação não encontrada."};
    auto record = db_.queryParticipation(participationId);
    if (!record) return ParticipationServiceError{503, "persistence_unavailable", "Persistência de participação indisponível."};
    if (record->empty()) return ParticipationServiceError{404, "not_found", "Participação não encontrada."};
    return *record;
}

} // namespace sisterd
