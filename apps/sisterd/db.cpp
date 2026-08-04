#include "db.hpp"

#include <iostream>
#include <sstream>
#include <vector>

#ifdef SISTER_HAVE_LIBPQ
#include <libpq-fe.h>
#endif

namespace sisterd {

#ifdef SISTER_HAVE_LIBPQ

// ─── Implementação real com libpq ────────────────────────────────────────────

DbConn::DbConn(std::string url) : url_(std::move(url)) {
    connect();
}

DbConn::~DbConn() {
    disconnect();
}

bool DbConn::connected() const {
    return conn_ != nullptr && PQstatus(conn_) == CONNECTION_OK;
}

bool DbConn::ensureConnected() {
    if (connected()) return true;
    // Tenta reconectar se a conexão caiu
    if (conn_ != nullptr) {
        PQreset(conn_);
        if (PQstatus(conn_) == CONNECTION_OK) return true;
        disconnect();
    }
    connect();
    return connected();
}

void DbConn::connect() {
    conn_ = PQconnectdb(url_.c_str());
    if (PQstatus(conn_) != CONNECTION_OK) {
        std::cerr << "sisterd: db connection failed: "
                  << PQerrorMessage(conn_) << '\n';
        PQfinish(conn_);
        conn_ = nullptr;
    } else {
        std::cerr << "sisterd: db connected\n";
    }
}

void DbConn::disconnect() {
    if (conn_ != nullptr) {
        PQfinish(conn_);
        conn_ = nullptr;
    }
}

std::optional<std::string> DbConn::execJsonArray(const char* sql) {
    if (!ensureConnected()) return std::nullopt;

    PGresult* res = PQexec(conn_, sql);
    if (PQresultStatus(res) != PGRES_TUPLES_OK) {
        std::cerr << "sisterd: db query failed: "
                  << PQerrorMessage(conn_) << '\n';
        PQclear(res);
        return std::nullopt;
    }

    const int rows = PQntuples(res);
    if (rows == 0) {
        PQclear(res);
        return std::string("[]");
    }

    // Cada linha retorna uma única coluna com o JSON do objeto
    std::ostringstream out;
    out << '[';
    for (int i = 0; i < rows; ++i) {
        if (i > 0) out << ',';
        out << PQgetvalue(res, i, 0);
    }
    out << ']';
    PQclear(res);
    return out.str();
}

std::optional<std::string> DbConn::querySystems() {
    return execJsonArray(
        "SELECT row_to_json(t) FROM ("
        "  SELECT system_id AS id, system_name AS name, system_type AS type,"
        "         public_scope AS access_mode"
        "  FROM sister_systems ORDER BY created_at"
        ") t");
}

std::optional<std::string> DbConn::queryContracts() {
    return execJsonArray(
        "SELECT row_to_json(t) FROM ("
        "  SELECT contract_id AS name, contract_version AS version,"
        "         status AS required"
        "  FROM sister_contracts ORDER BY created_at"
        ") t");
}

std::optional<std::string> DbConn::queryEvidence() {
    return execJsonArray(
        "SELECT row_to_json(t) FROM ("
        "  SELECT evidence_id AS id, source_system_id AS system,"
        "         kind, uri, captured_at"
        "  FROM sister_evidence ORDER BY captured_at DESC LIMIT 100"
        ") t");
}

std::optional<std::string> DbConn::queryDiagnostics() {
    return execJsonArray(
        "SELECT row_to_json(t) FROM ("
        "  SELECT service_name AS service, status, score, summary, observed_at"
        "  FROM sister_service_diagnostics ORDER BY observed_at DESC"
        ") t");
}

std::optional<std::string> DbConn::queryOperationalBase() {
    if (!ensureConnected()) return std::nullopt;
    PGresult* result = PQexec(conn_,
        "WITH approved AS ("
        "  SELECT d.integration_id, d.version, d.objective, d.contract, d.offer_id, d.requirement_id,"
        "         d.approved_by, d.approved_at, o.subsystem_id AS source_subsystem_id,"
        "         r.subsystem_id AS target_subsystem_id"
        "  FROM sister_integration_definitions d"
        "  JOIN sister_capability_offers o ON o.offer_id = d.offer_id"
        "  JOIN sister_capability_requirements r ON r.requirement_id = d.requirement_id"
        "  WHERE d.approval_status = 'approved' AND d.signature_verified"
        "    AND o.signature_verified AND r.signature_verified"
        "), candidates AS ("
        "  SELECT d.integration_id, d.version, d.objective, d.approval_status, d.signature_verified,"
        "         d.offer_id, d.requirement_id, o.subsystem_id AS source_subsystem_id,"
        "         r.subsystem_id AS target_subsystem_id"
        "  FROM sister_integration_definitions d"
        "  JOIN sister_capability_offers o ON o.offer_id = d.offer_id"
        "  JOIN sister_capability_requirements r ON r.requirement_id = d.requirement_id"
        "  WHERE NOT (d.approval_status = 'approved' AND d.signature_verified"
        "    AND o.signature_verified AND r.signature_verified)"
        "  ORDER BY d.registered_at DESC LIMIT 20"
        "), latest_assessment AS ("
        "  SELECT DISTINCT ON (integration_id, integration_version)"
        "         integration_id, integration_version, result, recommendation_action,"
        "         human_decision_required, assessment, assessed_at"
        "  FROM sister_integration_assessments"
        "  ORDER BY integration_id, integration_version, assessed_at DESC"
        "), latest_execution AS ("
        "  SELECT DISTINCT ON (integration_id, integration_version)"
        "         integration_id, integration_version, execution_id, status, execution, finished_at, started_at"
        "  FROM sister_integration_executions"
        "  ORDER BY integration_id, integration_version, registered_at DESC"
        ")"
        "SELECT jsonb_build_object("
        "  'schema', 'sister.operational-base/0.1.0',"
        "  'capability_source', jsonb_build_object("
        "    'source', 'postgresql',"
        "    'signed_contracts_verified', EXISTS (SELECT 1 FROM approved),"
        "    'verification_status', CASE WHEN EXISTS (SELECT 1 FROM approved) THEN 'verified' ELSE 'no_approved_signed_contracts' END"
        "  ),"
        "  'offers', COALESCE((SELECT jsonb_agg(jsonb_build_object("
        "    'id', offer_id,"
        "    'subsystem_id', subsystem_id,"
        "    'capability', capability,"
        "    'produces', COALESCE(contract->'produces', '[]'::jsonb),"
        "    'contract_schema', contract->'contract'->>'schema_id',"
        "    'contract_version', contract->'contract'->>'version',"
        "    'status', upper(status),"
        "    'signature_verified', signature_verified"
        "  ) ORDER BY registered_at DESC) FROM sister_capability_offers), '[]'::jsonb),"
        "  'requirements', COALESCE((SELECT jsonb_agg(jsonb_build_object("
        "    'id', requirement_id,"
        "    'subsystem_id', subsystem_id,"
        "    'needed_capability', needed_capability,"
        "    'purpose', contract->>'purpose',"
        "    'expected_schema', contract->'expected_contract'->>'schema_id',"
        "    'expected_version', contract->'expected_contract'->>'version',"
        "    'status', upper(status),"
        "    'signature_verified', signature_verified"
        "  ) ORDER BY registered_at DESC) FROM sister_capability_requirements), '[]'::jsonb),"
        "  'purpose', jsonb_build_object("
        "    'title', COALESCE((SELECT objective FROM approved LIMIT 1), 'Propósito operacional não publicado'),"
        "    'status', CASE WHEN EXISTS (SELECT 1 FROM approved) THEN 'APPROVED' ELSE 'MISSING' END,"
        "    'detail', 'Fonte autoritativa: PostgreSQL do sisterd'"
        "  ),"
        "  'functions', COALESCE((SELECT jsonb_agg(jsonb_build_object("
        "    'id', integration_id,"
        "    'title', 'executar integração aprovada ' || source_subsystem_id || ' -> ' || target_subsystem_id"
        "  )) FROM approved), '[]'::jsonb),"
        "  'process', jsonb_build_object("
        "    'title', COALESCE((SELECT integration_id FROM approved LIMIT 1), 'Processo aprovado não publicado'),"
        "    'status', CASE WHEN EXISTS (SELECT 1 FROM approved) THEN 'APPROVED' ELSE 'MISSING' END,"
        "    'detail', 'Apenas definições aprovadas e com assinatura verificada promovem processo operacional'"
        "  ),"
        "  'approval', jsonb_build_object("
        "    'status', CASE WHEN EXISTS (SELECT 1 FROM approved) THEN 'APPROVED' ELSE 'MISSING' END,"
        "    'authority', 'integration.approve',"
        "    'detail', CASE WHEN EXISTS (SELECT 1 FROM approved) THEN 'Contrato aprovado e verificado' ELSE 'Nenhuma definição assinada e aprovada' END"
        "  ),"
        "  'instance', jsonb_build_object('status', 'NOT_CREATED', 'detail', 'Execuções operacionais dependem de definição aprovada'),"
        "  'execution', jsonb_build_object("
        "    'status', COALESCE((SELECT upper(status) FROM latest_execution LIMIT 1), 'NOT_RECORDED'),"
        "    'expected', 'Execução de integração aprovada',"
        "    'observed', COALESCE((SELECT execution_id || ' · ' || status FROM latest_execution LIMIT 1), 'Sem execução promovida')"
        "  ),"
        "  'observation', jsonb_build_object("
        "    'status', CASE WHEN EXISTS (SELECT 1 FROM latest_execution) THEN 'COMPLETED' ELSE 'NOT_RECORDED' END,"
        "    'evidence', COALESCE((SELECT execution->'observations' FROM latest_execution LIMIT 1), '[]'::jsonb)"
        "  ),"
        "  'assessment', jsonb_build_object("
        "    'status', COALESCE((SELECT upper(result) FROM latest_assessment LIMIT 1), 'NOT_AVAILABLE'),"
        "    'comparison', CASE WHEN EXISTS (SELECT 1 FROM candidates) THEN 'Há integração candidata registrada, mas falta assinatura/aprovação completa.' ELSE 'Sem contratos de integração registrados.' END,"
        "    'recommendation', CASE WHEN EXISTS (SELECT 1 FROM candidates) THEN 'Revisar, assinar e aprovar a integração candidata antes de promover capacidade operacional.' ELSE 'Registrar oferta, requisito e definição de integração assinados.' END,"
        "    'human_decision', 'aprovar ou rejeitar integração candidata'"
        "  ),"
        "  'candidates', COALESCE((SELECT jsonb_agg(jsonb_build_object("
        "    'id', integration_id,"
        "    'version', version,"
        "    'title', 'Integração candidata ' || source_subsystem_id || ' -> ' || target_subsystem_id,"
        "    'source_offer', offer_id,"
        "    'target_requirement', requirement_id,"
        "    'objective', objective,"
        "    'status', CASE WHEN signature_verified THEN upper(approval_status) ELSE 'AWAITING_SIGNATURE_AND_APPROVAL' END,"
        "    'recommendation', 'Assinar oferta, requisito e definição; então registrar aprovação humana com autoridade integration.approve.'"
        "  )) FROM candidates), '[]'::jsonb),"
        "  'capabilities', COALESCE((SELECT jsonb_agg(jsonb_build_object("
        "    'id', integration_id,"
        "    'version', version,"
        "    'title', 'integrar ' || source_subsystem_id || ' -> ' || target_subsystem_id,"
        "    'status', 'APROVADA',"
        "    'purpose', objective,"
        "    'process', integration_id,"
        "    'functions', jsonb_build_array('executar integração aprovada', 'registrar evidências', 'avaliar resultado'),"
        "    'criteria', COALESCE(contract->'success_criteria', '[]'::jsonb),"
        "    'contracts', jsonb_build_array(offer_id, requirement_id, integration_id),"
        "    'observations', COALESCE((SELECT execution->'observations' FROM latest_execution e WHERE e.integration_id = approved.integration_id AND e.integration_version = approved.version LIMIT 1), jsonb_build_array('Nenhuma observação registrada'))"
        "  )) FROM approved), '[]'::jsonb)"
        ")::text");
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        std::cerr << "sisterd: operational base query failed: " << PQerrorMessage(conn_) << '\n';
        PQclear(result);
        return std::nullopt;
    }
    std::string response = PQgetvalue(result, 0, 0);
    PQclear(result);
    return response;
}

std::optional<std::string> DbConn::decideIntegration(
    const std::string& integrationId,
    const std::string& version,
    const std::string& decision,
    const std::string& decidedBy,
    const std::string& rationale) {
    if (!ensureConnected()) return std::nullopt;
    if (decision != "approved" && decision != "rejected") return std::nullopt;

    const char* params[5] = {
        integrationId.c_str(),
        version.c_str(),
        decision.c_str(),
        decidedBy.c_str(),
        rationale.c_str()
    };
    PGresult* result = PQexecParams(conn_,
        "WITH target AS ("
        "  SELECT integration_id, version, offer_id, requirement_id"
        "  FROM sister_integration_definitions"
        "  WHERE integration_id = $1 AND version = $2"
        "  FOR UPDATE"
        "), verify_offer AS ("
        "  UPDATE sister_capability_offers o SET"
        "    signature_verified = CASE WHEN $3 = 'approved' THEN true ELSE signature_verified END,"
        "    status = CASE WHEN $3 = 'approved' THEN 'active' ELSE status END"
        "  FROM target t WHERE o.offer_id = t.offer_id RETURNING o.offer_id"
        "), verify_requirement AS ("
        "  UPDATE sister_capability_requirements r SET"
        "    signature_verified = CASE WHEN $3 = 'approved' THEN true ELSE signature_verified END,"
        "    status = CASE WHEN $3 = 'approved' THEN 'satisfied' ELSE status END"
        "  FROM target t WHERE r.requirement_id = t.requirement_id RETURNING r.requirement_id"
        "), updated AS ("
        "  UPDATE sister_integration_definitions d SET"
        "    approval_status = $3,"
        "    signature_verified = CASE WHEN $3 = 'approved' THEN true ELSE d.signature_verified END,"
        "    approved_by = $4,"
        "    approved_at = now(),"
        "    contract = jsonb_set("
        "      d.contract,"
        "      '{approval}',"
        "      jsonb_build_object("
        "        'status', $3,"
        "        'responsible', $4,"
        "        'authority', 'integration.approve',"
        "        'rationale', $5,"
        "        'decided_at', now()"
        "      ),"
        "      true"
        "    )"
        "  WHERE d.integration_id = $1 AND d.version = $2"
        "  RETURNING d.integration_id, d.version, d.approval_status, d.approved_by, d.approved_at"
        "), decision_record AS ("
        "  INSERT INTO sister_integration_decisions ("
        "    decision_id, integration_id, integration_version, decision, decided_by,"
        "    authority, rationale, decision_record"
        "  )"
        "  SELECT"
        "    'decision-' || $1 || '-' || $2 || '-' || replace(extract(epoch from clock_timestamp())::text, '.', '-'),"
        "    integration_id, version, $3, $4, 'integration.approve', $5,"
        "    jsonb_build_object("
        "      'schema', 'sister.integration-decision/1.0.0',"
        "      'integration_id', integration_id,"
        "      'version', version,"
        "      'decision', $3,"
        "      'decided_by', $4,"
        "      'authority', 'integration.approve',"
        "      'rationale', $5,"
        "      'decided_at', approved_at"
        "    )"
        "  FROM updated"
        "  RETURNING decision_id"
        ")"
        "SELECT jsonb_build_object("
        "  'integration_id', u.integration_id,"
        "  'version', u.version,"
        "  'decision', u.approval_status,"
        "  'decided_by', u.approved_by,"
        "  'decided_at', u.approved_at,"
        "  'decision_id', d.decision_id"
        ")::text"
        " FROM updated u JOIN decision_record d ON true",
        5, nullptr, params, nullptr, nullptr, 0);

    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        std::cerr << "sisterd: integration decision failed: "
                  << PQerrorMessage(conn_) << '\n';
        PQclear(result);
        return std::nullopt;
    }
    std::string response = PQgetvalue(result, 0, 0);
    PQclear(result);
    return response;
}

bool DbConn::integrationApproved(const std::string& integrationId, const std::string& version) {
    if (!ensureConnected()) return false;
    const char* params[2] = {integrationId.c_str(), version.c_str()};
    PGresult* result = PQexecParams(conn_,
        "SELECT EXISTS ("
        "  SELECT 1 FROM sister_integration_definitions d"
        "  JOIN sister_capability_offers o ON o.offer_id = d.offer_id"
        "  JOIN sister_capability_requirements r ON r.requirement_id = d.requirement_id"
        "  WHERE d.integration_id = $1 AND d.version = $2"
        "    AND d.approval_status = 'approved' AND d.signature_verified"
        "    AND o.signature_verified AND r.signature_verified"
        ")",
        2, nullptr, params, nullptr, nullptr, 0);
    const bool approved = PQresultStatus(result) == PGRES_TUPLES_OK &&
        PQntuples(result) == 1 && std::string(PQgetvalue(result, 0, 0)) == "t";
    PQclear(result);
    return approved;
}

std::optional<std::string> DbConn::recordIntegrationExecution(
    const std::string& integrationId,
    const std::string& version,
    const std::string& executionId,
    const std::string& status,
    const std::string& contractDigest,
    const std::string& executionJson,
    const std::string& assessmentId,
    const std::string& result,
    const std::string& recommendationAction,
    bool humanDecisionRequired,
    const std::string& assessmentJson) {
    if (!ensureConnected()) return std::nullopt;
    const std::string human = humanDecisionRequired ? "true" : "false";
    const char* params[11] = {
        integrationId.c_str(), version.c_str(), executionId.c_str(),
        status.c_str(), contractDigest.c_str(), executionJson.c_str(),
        assessmentId.c_str(), result.c_str(), recommendationAction.c_str(),
        human.c_str(), assessmentJson.c_str()
    };
    PGresult* pgResult = PQexecParams(conn_,
        "WITH approved AS ("
        "  SELECT d.integration_id, d.version"
        "  FROM sister_integration_definitions d"
        "  JOIN sister_capability_offers o ON o.offer_id = d.offer_id"
        "  JOIN sister_capability_requirements r ON r.requirement_id = d.requirement_id"
        "  WHERE d.integration_id = $1 AND d.version = $2"
        "    AND d.approval_status = 'approved' AND d.signature_verified"
        "    AND o.signature_verified AND r.signature_verified"
        "), inserted_execution AS ("
        "  INSERT INTO sister_integration_executions ("
        "    execution_id, integration_id, integration_version, status,"
        "    contract_digest, execution, started_at, finished_at"
        "  )"
        "  SELECT $3, integration_id, version, $4, $5, $6::jsonb,"
        "         now(), CASE WHEN $4 IN ('completed', 'failed', 'cancelled') THEN now() ELSE NULL END"
        "  FROM approved"
        "  RETURNING execution_id, integration_id, integration_version, status"
        "), inserted_assessment AS ("
        "  INSERT INTO sister_integration_assessments ("
        "    assessment_id, integration_id, integration_version, execution_id,"
        "    result, recommendation_action, human_decision_required, assessment, assessed_at"
        "  )"
        "  SELECT $7, integration_id, integration_version, execution_id,"
        "         $8, $9, $10::boolean, $11::jsonb, now()"
        "  FROM inserted_execution"
        "  RETURNING assessment_id, result, recommendation_action"
        ")"
        "SELECT jsonb_build_object("
        "  'execution_id', e.execution_id,"
        "  'integration_id', e.integration_id,"
        "  'version', e.integration_version,"
        "  'status', e.status,"
        "  'assessment_id', a.assessment_id,"
        "  'assessment_result', a.result,"
        "  'recommendation_action', a.recommendation_action"
        ")::text"
        " FROM inserted_execution e JOIN inserted_assessment a ON true",
        11, nullptr, params, nullptr, nullptr, 0);
    if (PQresultStatus(pgResult) != PGRES_TUPLES_OK || PQntuples(pgResult) != 1) {
        std::cerr << "sisterd: integration execution record failed: "
                  << PQerrorMessage(conn_) << '\n';
        PQclear(pgResult);
        return std::nullopt;
    }
    std::string response = PQgetvalue(pgResult, 0, 0);
    PQclear(pgResult);
    return response;
}

std::optional<std::string> DbConn::registerParticipationProposal(const ParticipationProposal& proposal) {
    if (!ensureConnected()) return std::nullopt;
    const char* values[] = {proposal.participation_id.c_str(), proposal.participant_system_id.c_str(),
        proposal.contract_version.c_str(), proposal.contract_digest.c_str(), proposal.contract_json.c_str(),
        proposal.proposed_by.c_str(), proposal.authentication_source.c_str(),
        proposal.source_commit.empty() ? nullptr : proposal.source_commit.c_str()};
    PGresult* result = PQexecParams(conn_,
        "INSERT INTO sister_participation_contracts "
        "(participation_id, participant_system_id, contract_version, contract_digest, state, contract, proposed_by, authentication_source, source_commit) "
        "VALUES ($1, $2, $3, $4, 'proposed', $5::jsonb, $6, $7, $8) "
        "RETURNING row_to_json(sister_participation_contracts)", 8, nullptr, values, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        std::cerr << "sisterd: participation insert failed: " << PQerrorMessage(conn_) << '\n';
        PQclear(result);
        return std::nullopt;
    }
    std::string response = PQgetvalue(result, 0, 0);
    PQclear(result);
    return response;
}

std::optional<std::string> DbConn::queryParticipation(const std::string& participationId) {
    if (!ensureConnected()) return std::nullopt;
    const char* values[] = {participationId.c_str()};
    PGresult* result = PQexecParams(conn_,
        "SELECT row_to_json(t) FROM (SELECT participation_id, participant_system_id, contract_version, "
        "contract_digest, state, contract, proposed_by, authentication_source, source_commit, created_at, updated_at "
        "FROM sister_participation_contracts WHERE participation_id = $1) t", 1, nullptr, values, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK) {
        std::cerr << "sisterd: participation query failed: " << PQerrorMessage(conn_) << '\n';
        PQclear(result);
        return std::nullopt;
    }
    if (PQntuples(result) == 0) {
        PQclear(result);
        return std::string();
    }
    std::string response = PQgetvalue(result, 0, 0);
    PQclear(result);
    return response;
}

std::optional<std::string> DbConn::registerParticipationAssessment(
    const std::string& assessmentId, const std::string& participationId,
    const std::string& contractDigest, const std::string& evaluatedCommit,
    const std::string& assessmentJson) {
    if (!ensureConnected()) return std::nullopt;
    const char* values[] = {assessmentId.c_str(), participationId.c_str(), contractDigest.c_str(),
        evaluatedCommit.c_str(), assessmentJson.c_str()};
    PGresult* result = PQexecParams(conn_,
        "INSERT INTO sister_participation_assessments "
        "(assessment_id, participation_id, contract_digest, evaluated_commit, result, gate_effect, assessment) "
        "VALUES ($1, $2, $3, $4, 'PASS', 'none', $5::jsonb) "
        "RETURNING row_to_json(sister_participation_assessments)", 5, nullptr, values, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        std::cerr << "sisterd: participation assessment insert failed: " << PQerrorMessage(conn_) << '\n';
        PQclear(result);
        return std::nullopt;
    }
    std::string response = PQgetvalue(result, 0, 0);
    PQclear(result);
    return response;
}

std::optional<std::string> DbConn::queryParticipationAssessments(const std::string& participationId) {
    if (!ensureConnected()) return std::nullopt;
    const char* values[] = {participationId.c_str()};
    PGresult* result = PQexecParams(conn_,
        "SELECT COALESCE(jsonb_agg(t ORDER BY t.created_at), '[]'::jsonb) FROM ("
        "SELECT assessment_id, participation_id, contract_digest, evaluated_commit, result, gate_effect, assessment, created_at "
        "FROM sister_participation_assessments WHERE participation_id = $1) t", 1, nullptr, values, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        PQclear(result);
        return std::nullopt;
    }
    std::string response = PQgetvalue(result, 0, 0);
    PQclear(result);
    return response;
}

#else

// ─── Stub sem libpq — compila sem banco disponível ───────────────────────────

DbConn::DbConn(std::string url) : url_(std::move(url)) {
    std::cerr << "sisterd: compiled without libpq — running without database\n";
}

DbConn::~DbConn() = default;

bool DbConn::connected() const          { return false; }
bool DbConn::ensureConnected()          { return false; }
void DbConn::connect()                  {}
void DbConn::disconnect()               {}

std::optional<std::string> DbConn::execJsonArray(const char*) {
    return std::nullopt;
}
std::optional<std::string> DbConn::querySystems()     { return std::nullopt; }
std::optional<std::string> DbConn::queryContracts()   { return std::nullopt; }
std::optional<std::string> DbConn::queryEvidence()    { return std::nullopt; }
std::optional<std::string> DbConn::queryDiagnostics() { return std::nullopt; }
std::optional<std::string> DbConn::queryOperationalBase() { return std::nullopt; }
std::optional<std::string> DbConn::decideIntegration(const std::string&, const std::string&, const std::string&, const std::string&, const std::string&) { return std::nullopt; }
bool DbConn::integrationApproved(const std::string&, const std::string&) { return false; }
std::optional<std::string> DbConn::recordIntegrationExecution(const std::string&, const std::string&, const std::string&, const std::string&, const std::string&, const std::string&, const std::string&, const std::string&, const std::string&, bool, const std::string&) { return std::nullopt; }
std::optional<std::string> DbConn::registerParticipationProposal(const ParticipationProposal&) { return std::nullopt; }
std::optional<std::string> DbConn::queryParticipation(const std::string&) { return std::nullopt; }
std::optional<std::string> DbConn::registerParticipationAssessment(const std::string&, const std::string&, const std::string&, const std::string&, const std::string&) { return std::nullopt; }
std::optional<std::string> DbConn::queryParticipationAssessments(const std::string&) { return std::nullopt; }

#endif

} // namespace sisterd
