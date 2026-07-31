#include "maturity_routes.hpp"
#include <fstream>
#include <sstream>

namespace sisterd {
namespace api {

namespace {
    std::string jsonError(int code, const std::string& title, const std::string& detail) {
        return "{\n  \"error\": {\n    \"code\": " + std::to_string(code) + ",\n    \"title\": \"" + title + "\",\n    \"detail\": \"" + detail + "\"\n  }\n}";
    }

    bool hasJsonStringField(const std::string& json, const std::string& field, const std::string& expectedValue) {
        std::string pattern = "\"" + field + "\"";
        auto pos = json.find(pattern);
        if (pos == std::string::npos) return false;
        pos = json.find(":", pos);
        if (pos == std::string::npos) return false;
        pos = json.find("\"", pos);
        if (pos == std::string::npos) return false;
        auto endPos = json.find("\"", pos + 1);
        if (endPos == std::string::npos) return false;
        std::string value = json.substr(pos + 1, endPos - pos - 1);
        return value == expectedValue;
    }
}

RouteResponse getMaturityComponents(const std::optional<AuthUser>& actor, const std::filesystem::path& maturityRoot) {
    if (!actor) {
        return {401, "Unauthorized", "application/json; charset=utf-8", jsonError(401, "Unauthorized", "Autenticação necessária.")};
    }
    
    // Check permission (role must be admin to read components)
    // The user requested `sister.maturity.read` capability, but auth.hpp currently uses `role == "admin"`.
    // Assuming `role == "admin"` gives `sister.maturity.read` implicitly in the current monolithic logic.
    if (actor->role != "admin") {
        return {403, "Forbidden", "application/json; charset=utf-8", jsonError(403, "Forbidden", "Acesso restrito à equipe administrativa.")};
    }

    std::filesystem::path componentsPath = maturityRoot / "components.json";
    
    std::error_code ec;
    auto status = std::filesystem::symlink_status(componentsPath, ec);
    if (ec || !std::filesystem::exists(status) || !std::filesystem::is_regular_file(status)) {
        return {404, "Not Found", "application/json; charset=utf-8", jsonError(404, "Not Found", "Índice de componentes não foi publicado.")};
    }

    auto size = std::filesystem::file_size(componentsPath, ec);
    if (ec || size == 0 || size > 10 * 1024 * 1024) { // 10MB limit
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "O arquivo do índice é inválido ou excede o limite de tamanho.")};
    }

    std::ifstream input(componentsPath, std::ios::binary);
    if (!input) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "Falha ao ler o arquivo de índice.")};
    }

    std::string body(static_cast<std::size_t>(size), '\0');
    if (!input.read(body.data(), static_cast<std::streamsize>(size))) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "Leitura incompleta do índice.")};
    }

    const auto first = body.find_first_not_of(" \t\r\n");
    const auto last = body.find_last_not_of(" \t\r\n");
    if (first == std::string::npos || body[first] != '{' || body[last] != '}' ||
        !hasJsonStringField(body, "schema", "sister.maturity-components/1.0.0")) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "Schema inválido no índice de componentes.")};
    }

    return {200, "OK", "application/json; charset=utf-8", std::move(body)};
}

RouteResponse getMaturityCatalog(const std::optional<AuthUser>& actor, const std::filesystem::path& maturityRoot) {
    if (!actor) {
        return {401, "Unauthorized", "application/json; charset=utf-8", jsonError(401, "Unauthorized", "Autenticação necessária.")};
    }
    if (actor->role != "admin") {
        return {403, "Forbidden", "application/json; charset=utf-8", jsonError(403, "Forbidden", "Acesso restrito à equipe administrativa.")};
    }

    std::filesystem::path catalogPath = maturityRoot / "catalog.json";
    std::error_code ec;
    auto status = std::filesystem::symlink_status(catalogPath, ec);
    if (ec || !std::filesystem::exists(status) || !std::filesystem::is_regular_file(status)) {
        return {404, "Not Found", "application/json; charset=utf-8", jsonError(404, "Not Found", "Catálogo de checks não foi publicado.")};
    }

    auto size = std::filesystem::file_size(catalogPath, ec);
    if (ec || size == 0 || size > 10 * 1024 * 1024) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "O catálogo é inválido ou excede o limite de tamanho.")};
    }

    std::ifstream input(catalogPath, std::ios::binary);
    if (!input) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "Falha ao ler o catálogo.")};
    }

    std::string body(static_cast<std::size_t>(size), '\0');
    if (!input.read(body.data(), static_cast<std::streamsize>(size))) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "Leitura incompleta do catálogo.")};
    }

    const auto first = body.find_first_not_of(" \t\r\n");
    const auto last = body.find_last_not_of(" \t\r\n");
    if (first == std::string::npos || body[first] != '{' || body[last] != '}' ||
        !hasJsonStringField(body, "schema", "sister.maturity-catalog/1.0.0")) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "Schema inválido no catálogo de checks.")};
    }

    return {200, "OK", "application/json; charset=utf-8", std::move(body)};
}

RouteResponse getQualityStatus(const std::optional<AuthUser>& actor, const std::filesystem::path& maturityRoot) {
    if (!actor) {
        return {401, "Unauthorized", "application/json; charset=utf-8", jsonError(401, "Unauthorized", "Autenticação necessária.")};
    }
    if (actor->role != "admin") {
        return {403, "Forbidden", "application/json; charset=utf-8", jsonError(403, "Forbidden", "Acesso restrito à equipe administrativa.")};
    }

    const std::filesystem::path qualityPath = maturityRoot / "quality.json";
    std::error_code ec;
    const auto status = std::filesystem::symlink_status(qualityPath, ec);
    if (ec || !std::filesystem::exists(status) || !std::filesystem::is_regular_file(status)) {
        return {404, "Not Found", "application/json; charset=utf-8", jsonError(404, "Not Found", "Nenhuma execução da suíte de qualidade foi publicada.")};
    }
    const auto size = std::filesystem::file_size(qualityPath, ec);
    if (ec || size == 0 || size > 10 * 1024 * 1024) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "O relatório de qualidade é inválido ou excede o limite de tamanho.")};
    }
    std::ifstream input(qualityPath, std::ios::binary);
    std::string body(static_cast<std::size_t>(size), '\0');
    if (!input || !input.read(body.data(), static_cast<std::streamsize>(size))) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "Falha ao ler o relatório de qualidade.")};
    }
    const auto first = body.find_first_not_of(" \t\r\n");
    const auto last = body.find_last_not_of(" \t\r\n");
    if (first == std::string::npos || body[first] != '{' || body[last] != '}' ||
        !hasJsonStringField(body, "schema", "sister.quality-status/1.0.0")) {
        return {503, "Service Unavailable", "application/json; charset=utf-8", jsonError(503, "Service Unavailable", "Schema inválido no relatório de qualidade.")};
    }
    return {200, "OK", "application/json; charset=utf-8", std::move(body)};
}

} // namespace api
} // namespace sisterd
