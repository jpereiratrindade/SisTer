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
std::optional<std::string> DbConn::registerParticipationProposal(const ParticipationProposal&) { return std::nullopt; }
std::optional<std::string> DbConn::queryParticipation(const std::string&) { return std::nullopt; }

#endif

} // namespace sisterd
