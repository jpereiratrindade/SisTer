#pragma once

#include <optional>
#include <string>

// Forward declaration — evita expor libpq em cabeçalhos de uso geral
struct pg_conn;

namespace sisterd {

class DbConn {
public:
    // Constrói sem conectar. Chame ensureConnected() para tentar a conexão.
    explicit DbConn(std::string url);
    ~DbConn();

    // Não copiável — gerencia um recurso único
    DbConn(const DbConn&) = delete;
    DbConn& operator=(const DbConn&) = delete;

    // Retorna true se a conexão está ativa e verificada
    bool connected() const;

    // Tenta (re)conectar silenciosamente; retorna true em sucesso
    bool ensureConnected();

    // Retorna JSON pronto para resposta HTTP; std::nullopt se não conectado
    std::optional<std::string> querySystems();
    std::optional<std::string> queryContracts();
    std::optional<std::string> queryEvidence();
    std::optional<std::string> queryDiagnostics();

private:
    std::string url_;
    pg_conn* conn_ = nullptr;

    void connect();
    void disconnect();

    // Executa SQL e retorna um array JSON com os resultados.
    // Retorna std::nullopt se a query falhar.
    std::optional<std::string> execJsonArray(const char* sql);
};

} // namespace sisterd
