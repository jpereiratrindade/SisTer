#include "auth.hpp"
#include "studio_client.hpp"

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <cerrno>
#include <cctype>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

constexpr std::size_t maxRequestSize = 65536;
constexpr std::string_view sessionCookie = "sister_session";
volatile std::sig_atomic_t keepRunning = 1;

struct HttpRequest {
    std::string method;
    std::string path;
    std::unordered_map<std::string, std::string> headers;
    std::string body;
};

void handleSignal(int) {
    keepRunning = 0;
}

std::string lowercase(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char character) {
        return static_cast<char>(std::tolower(character));
    });
    return value;
}

std::string trim(std::string value) {
    const auto first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return {};
    const auto last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

std::string readFile(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("file not found");
    std::ostringstream buffer;
    buffer << in.rdbuf();
    return buffer.str();
}

std::string contentType(const std::filesystem::path& path) {
    const auto ext = path.extension().string();
    if (ext == ".html") return "text/html; charset=utf-8";
    if (ext == ".css") return "text/css; charset=utf-8";
    if (ext == ".js") return "application/javascript; charset=utf-8";
    if (ext == ".json") return "application/json; charset=utf-8";
    if (ext == ".svg") return "image/svg+xml";
    if (ext == ".png") return "image/png";
    if (ext == ".jpg" || ext == ".jpeg") return "image/jpeg";
    return "application/octet-stream";
}

std::string httpResponse(
    int status,
    std::string_view reason,
    std::string_view body,
    std::string_view type,
    const std::vector<std::pair<std::string, std::string>>& headers = {}) {
    std::ostringstream out;
    out << "HTTP/1.1 " << status << ' ' << reason << "\r\n"
        << "Content-Type: " << type << "\r\n"
        << "Content-Length: " << body.size() << "\r\n"
        << "Connection: close\r\n"
        << "X-Content-Type-Options: nosniff\r\n"
        << "Referrer-Policy: same-origin\r\n";
    for (const auto& [name, value] : headers) out << name << ": " << value << "\r\n";
    out << "\r\n" << body;
    return out.str();
}

std::string jsonEscape(std::string_view value) {
    std::string escaped;
    escaped.reserve(value.size());
    for (const char character : value) {
        switch (character) {
            case '\\': escaped += "\\\\"; break;
            case '"': escaped += "\\\""; break;
            case '\n': escaped += "\\n"; break;
            case '\r': escaped += "\\r"; break;
            case '\t': escaped += "\\t"; break;
            default: escaped += character; break;
        }
    }
    return escaped;
}

std::optional<std::string> jsonField(const std::string& body, const std::string& key) {
    const auto marker = '"' + key + '"';
    auto position = body.find(marker);
    if (position == std::string::npos) return std::nullopt;
    position = body.find(':', position + marker.size());
    if (position == std::string::npos) return std::nullopt;
    position = body.find('"', position + 1);
    if (position == std::string::npos) return std::nullopt;

    std::string value;
    bool escaped = false;
    for (++position; position < body.size(); ++position) {
        const char character = body[position];
        if (escaped) {
            switch (character) {
                case 'n': value += '\n'; break;
                case 'r': value += '\r'; break;
                case 't': value += '\t'; break;
                default: value += character; break;
            }
            escaped = false;
        } else if (character == '\\') {
            escaped = true;
        } else if (character == '"') {
            return value;
        } else {
            value += character;
        }
    }
    return std::nullopt;
}

std::string cookieValue(const HttpRequest& request, std::string_view name) {
    const auto found = request.headers.find("cookie");
    if (found == request.headers.end()) return {};
    std::istringstream cookies(found->second);
    std::string item;
    while (std::getline(cookies, item, ';')) {
        item = trim(item);
        const auto separator = item.find('=');
        if (separator != std::string::npos && item.substr(0, separator) == name) {
            return item.substr(separator + 1);
        }
    }
    return {};
}

std::optional<HttpRequest> readRequest(int client) {
    std::string raw;
    std::size_t expectedSize = 0;
    while (raw.size() < maxRequestSize) {
        char buffer[8192];
        const auto received = recv(client, buffer, sizeof(buffer), 0);
        if (received <= 0) return std::nullopt;
        raw.append(buffer, static_cast<std::size_t>(received));

        const auto headerEnd = raw.find("\r\n\r\n");
        if (headerEnd == std::string::npos) continue;
        if (expectedSize == 0) {
            const auto lengthMarker = lowercase(raw.substr(0, headerEnd)).find("content-length:");
            std::size_t contentLength = 0;
            if (lengthMarker != std::string::npos) {
                const auto valueStart = lengthMarker + std::string("content-length:").size();
                const auto valueEnd = raw.find("\r\n", valueStart);
                try {
                    contentLength = std::stoul(trim(raw.substr(valueStart, valueEnd - valueStart)));
                } catch (const std::exception&) {
                    return std::nullopt;
                }
            }
            expectedSize = headerEnd + 4 + contentLength;
            if (expectedSize > maxRequestSize) return std::nullopt;
        }
        if (raw.size() >= expectedSize) break;
    }

    const auto headerEnd = raw.find("\r\n\r\n");
    if (headerEnd == std::string::npos) return std::nullopt;
    HttpRequest result;
    std::istringstream headers(raw.substr(0, headerEnd));
    std::string line;
    if (!std::getline(headers, line)) return std::nullopt;
    {
        std::istringstream startLine(line);
        startLine >> result.method >> result.path;
    }
    while (std::getline(headers, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        const auto separator = line.find(':');
        if (separator != std::string::npos) {
            result.headers[lowercase(trim(line.substr(0, separator)))] =
                trim(line.substr(separator + 1));
        }
    }
    result.body = raw.substr(headerEnd + 4);
    const auto query = result.path.find('?');
    if (query != std::string::npos) result.path.resize(query);
    return result;
}

std::string jsonHealth() {
    return R"({"status":"ok","service":"sisterd","version":"0.2.0","database":"not_connected"})";
}

std::string jsonContracts() {
    return R"([
  {"name":"System Manifest","version":"0.1.0","required":"Sim"},
  {"name":"CampoSync Package","version":"0.1.0","required":"Para ingestao offline"},
  {"name":"Evidence","version":"0.1.0","required":"Para dado promovido"},
  {"name":"Public Scope","version":"0.1.0","required":"Para classificacao de exposicao"},
  {"name":"Sister-Studio Integration","version":"1.0.0","required":"Para capacidades e saude sanitizada"}
])";
}

std::string jsonSystems() {
    return R"([
  {"id":"morfocampo","name":"MorfoCampo","type":"Campo","status":"Operacional","contract":"sister-contracts/0.1.0","access_url":"https://127.0.0.1:8011"},
  {"id":"droneops","name":"DroneOps","type":"Missao","status":"Em validacao","contract":"sister-contracts/0.1.0","access_url":"https://127.0.0.1:8012"},
  {"id":"camponode","name":"CampoNode","type":"Infraestrutura","status":"Planejado","contract":"sister-contracts/0.1.0","access_url":"https://camponode.local"},
  {"id":"radar_sister_resiliencia","name":"Radar-Sister Resiliencia","type":"Analitico","status":"Operacional","contract":"sister-contracts/0.1.0","access_url":"http://127.0.0.1:8765"},
  {"id":"sister_studio","name":"Sister-Studio","type":"Criativo","status":"Integrado","contract":"sister-studio.integration/1.0.0","access_url":"https://127.0.0.1:8443"}
])";
}

std::string jsonEvidence() {
    return R"([
  {"source":"MorfoCampo","object":"obs-001","kind":"photo","status":"proveniencia minima"},
  {"source":"DroneOps","object":"mission-terrace-01","kind":"spatial_layer","status":"referencia espacial"},
  {"source":"Radar-Sister Resiliencia","object":"shortlist-resiliencia-001","kind":"document","status":"triagem auditavel"}
])";
}

std::string jsonDiagnostics() {
    return R"([
  {"service":"Contract Registry","status":"operacional","score":100},
  {"service":"Package Ingest","status":"em validacao","score":78},
  {"service":"Evidence Store","status":"operacional","score":92},
  {"service":"Territorial Catalog","status":"planejado","score":45},
  {"service":"API Server","status":"inicial","score":40},
  {"service":"PostgreSQL/PostGIS/pgvector","status":"planejado","score":20}
])";
}

std::string routeApi(const std::string& path) {
    if (path == "/api/health") return jsonHealth();
    if (path == "/api/systems") return jsonSystems();
    if (path == "/api/contracts") return jsonContracts();
    if (path == "/api/evidence") return jsonEvidence();
    if (path == "/api/diagnostics") return jsonDiagnostics();
    if (path == "/api/integrations/sister-studio") {
        return sisterd::sisterStudioIntegrationJson();
    }
    return {};
}

std::string sanitizePath(const std::string& rawPath) {
    if (rawPath.empty() || rawPath == "/") return "/index.html";
    if (rawPath == "/login") return "/login.html";
    if (rawPath == "/admin/users") return "/admin.html";
    if (rawPath.find("..") != std::string::npos) return "/index.html";
    return rawPath;
}

std::string jsonUser(const sisterd::AuthUser& user) {
    return "{\"id\":\"" + jsonEscape(user.id) +
        "\",\"name\":\"" + jsonEscape(user.name) +
        "\",\"email\":\"" + jsonEscape(user.email) +
        "\",\"role\":\"" + jsonEscape(user.role) + "\"}";
}

void sendAll(int client, const std::string& response) {
    const char* data = response.data();
    std::size_t remaining = response.size();
    while (remaining > 0) {
        const ssize_t sent = send(client, data, remaining, 0);
        if (sent <= 0) return;
        data += sent;
        remaining -= static_cast<std::size_t>(sent);
    }
}

std::vector<std::pair<std::string, std::string>> sessionHeaders(const std::string& token) {
    return {
        {"Set-Cookie", std::string(sessionCookie) + "=" + token +
            "; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800"},
        {"Cache-Control", "no-store"}
    };
}

void sendJsonError(int client, int status, std::string_view reason, std::string_view detail) {
    sendAll(client, httpResponse(
        status,
        reason,
        "{\"detail\":\"" + jsonEscape(detail) + "\"}",
        "application/json; charset=utf-8",
        {{"Cache-Control", "no-store"}}));
}

bool handleAuthApi(
    int client,
    const HttpRequest& request,
    sisterd::AuthStore& auth) {
    if (request.path == "/api/auth/bootstrap" && request.method == "GET") {
        sendAll(client, httpResponse(
            200, "OK",
            auth.bootstrapOpen() ? R"({"open":true})" : R"({"open":false})",
            "application/json; charset=utf-8",
            {{"Cache-Control", "no-store"}}));
        return true;
    }

    if (request.path == "/api/auth/register" && request.method == "POST") {
        const auto name = jsonField(request.body, "name");
        const auto email = jsonField(request.body, "email");
        const auto password = jsonField(request.body, "password");
        if (!name || !email || !password) {
            sendJsonError(client, 400, "Bad Request", "Preencha nome, e-mail e senha.");
            return true;
        }
        try {
            const auto result = auth.registerAdmin(*name, *email, *password);
            if (!result) {
                sendJsonError(
                    client, 409, "Conflict",
                    "O cadastro inicial já foi concluído ou os dados são inválidos.");
                return true;
            }
            sendAll(client, httpResponse(
                201, "Created", R"({"status":"authenticated"})",
                "application/json; charset=utf-8",
                sessionHeaders(result->token)));
        } catch (const std::exception&) {
            sendJsonError(client, 500, "Internal Server Error", "Não foi possível criar a conta.");
        }
        return true;
    }

    if (request.path == "/api/auth/login" && request.method == "POST") {
        const auto email = jsonField(request.body, "email");
        const auto password = jsonField(request.body, "password");
        if (!email || !password) {
            sendJsonError(client, 400, "Bad Request", "Preencha e-mail e senha.");
            return true;
        }
        try {
            const auto result = auth.login(*email, *password);
            if (!result) {
                sendJsonError(client, 401, "Unauthorized", "Credenciais inválidas.");
                return true;
            }
            sendAll(client, httpResponse(
                200, "OK", R"({"status":"authenticated"})",
                "application/json; charset=utf-8",
                sessionHeaders(result->token)));
        } catch (const std::exception&) {
            sendJsonError(client, 500, "Internal Server Error", "Não foi possível entrar.");
        }
        return true;
    }

    if (request.path == "/api/auth/logout" && request.method == "POST") {
        auth.logout(cookieValue(request, sessionCookie));
        sendAll(client, httpResponse(
            204, "No Content", "", "application/json; charset=utf-8",
            {
                {"Set-Cookie", std::string(sessionCookie) +
                    "=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"},
                {"Cache-Control", "no-store"}
            }));
        return true;
    }
    return false;
}

void handleClient(
    int client,
    const std::filesystem::path& webRoot,
    sisterd::AuthStore& auth) {
    const auto request = readRequest(client);
    if (!request) {
        sendJsonError(client, 400, "Bad Request", "Requisição inválida.");
        return;
    }

    if (handleAuthApi(client, *request, auth)) return;

    const auto actor = auth.userForToken(cookieValue(*request, sessionCookie));
    if (request->path == "/api/me") {
        if (!actor) {
            sendJsonError(client, 401, "Unauthorized", "Autenticação necessária.");
            return;
        }
        sendAll(client, httpResponse(
            200, "OK", jsonUser(*actor), "application/json; charset=utf-8",
            {{"Cache-Control", "no-store"}}));
        return;
    }

    if (request->path == "/api/admin/users") {
        if (!actor) {
            sendJsonError(client, 401, "Unauthorized", "Autenticação necessária.");
            return;
        }
        if (actor->role != "admin") {
            sendJsonError(client, 403, "Forbidden", "Acesso restrito à equipe administrativa.");
            return;
        }
        if (request->method == "GET") {
            const auto users = auth.users();
            std::string body = "[";
            for (std::size_t index = 0; index < users.size(); ++index) {
                if (index > 0) body += ',';
                body += jsonUser(users[index]);
            }
            body += ']';
            sendAll(client, httpResponse(
                200, "OK", body, "application/json; charset=utf-8",
                {{"Cache-Control", "no-store"}}));
            return;
        }
        if (request->method == "POST") {
            const auto name = jsonField(request->body, "name");
            const auto email = jsonField(request->body, "email");
            const auto password = jsonField(request->body, "password");
            const auto role = jsonField(request->body, "role");
            if (!name || !email || !password || !role) {
                sendJsonError(client, 400, "Bad Request", "Preencha todos os campos.");
                return;
            }
            try {
                const auto created = auth.createUser(*name, *email, *password, *role);
                if (!created) {
                    sendJsonError(
                        client, 409, "Conflict",
                        "E-mail já cadastrado ou dados inválidos.");
                    return;
                }
                sendAll(client, httpResponse(
                    201, "Created", jsonUser(*created),
                    "application/json; charset=utf-8",
                    {{"Cache-Control", "no-store"}}));
            } catch (const std::exception&) {
                sendJsonError(client, 500, "Internal Server Error", "Não foi possível criar a conta.");
            }
            return;
        }
        sendJsonError(client, 405, "Method Not Allowed", "Método não permitido.");
        return;
    }

    if (request->path.rfind("/api/", 0) == 0) {
        if (request->method != "GET" && request->method != "HEAD") {
            sendJsonError(client, 405, "Method Not Allowed", "Método não permitido.");
            return;
        }
        const bool publicApi =
            request->path == "/api/health" || request->path == "/api/systems";
        if (!publicApi && !actor) {
            sendJsonError(client, 401, "Unauthorized", "Autenticação necessária.");
            return;
        }
        if (!publicApi && actor->role != "admin") {
            sendJsonError(client, 403, "Forbidden", "Acesso restrito à equipe administrativa.");
            return;
        }
        const auto body = routeApi(request->path);
        if (body.empty()) {
            sendJsonError(client, 404, "Not Found", "Recurso não encontrado.");
            return;
        }
        sendAll(client, httpResponse(
            200, "OK", body, "application/json; charset=utf-8",
            {{"Cache-Control", publicApi ? "no-cache" : "no-store"}}));
        return;
    }

    if (request->method != "GET" && request->method != "HEAD") {
        sendAll(client, httpResponse(
            405, "Method Not Allowed", "method not allowed", "text/plain; charset=utf-8"));
        return;
    }

    if (request->path == "/login" && actor) {
        sendAll(client, httpResponse(
            303, "See Other", "", "text/plain; charset=utf-8",
            {{"Location", "/"}, {"Cache-Control", "no-store"}}));
        return;
    }

    if (request->path == "/admin/users") {
        if (!actor) {
            sendAll(client, httpResponse(
                303, "See Other", "", "text/plain; charset=utf-8",
                {{"Location", "/login"}, {"Cache-Control", "no-store"}}));
            return;
        }
        if (actor->role != "admin") {
            sendAll(client, httpResponse(
                403, "Forbidden", "Acesso restrito à equipe administrativa.",
                "text/plain; charset=utf-8",
                {{"Cache-Control", "no-store"}}));
            return;
        }
    }

    const auto safePath = sanitizePath(request->path);
    const auto filePath = webRoot / safePath.substr(1);
    try {
        const auto body = readFile(filePath);
        sendAll(client, httpResponse(
            200, "OK", body, contentType(filePath),
            safePath == "/index.html" || safePath == "/login.html"
                ? std::vector<std::pair<std::string, std::string>>{{"Cache-Control", "no-cache"}}
                : std::vector<std::pair<std::string, std::string>>{}));
    } catch (const std::exception&) {
        sendAll(client, httpResponse(
            404, "Not Found", "not found", "text/plain; charset=utf-8"));
    }
}

int parsePort(const char* value) {
    if (value == nullptr) return 8000;
    return std::stoi(value);
}

} // namespace

int main(int argc, char** argv) {
    const int port = argc >= 2 ? std::stoi(argv[1]) : parsePort(std::getenv("SISTER_PORT"));
    const std::filesystem::path webRoot = argc >= 3 ? argv[2] : "web";
    const char* authFileEnv = std::getenv("SISTER_AUTH_FILE");
    const std::filesystem::path authFile =
        authFileEnv != nullptr ? authFileEnv : ".run/auth-users.tsv";
    sisterd::AuthStore auth(authFile);

    std::signal(SIGINT, handleSignal);
    std::signal(SIGTERM, handleSignal);

    const int server = socket(AF_INET, SOCK_STREAM, 0);
    if (server < 0) {
        std::cerr << "socket failed: " << std::strerror(errno) << '\n';
        return 1;
    }

    int opt = 1;
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    sockaddr_in address {};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(static_cast<uint16_t>(port));

    if (bind(server, reinterpret_cast<sockaddr*>(&address), sizeof(address)) < 0) {
        std::cerr << "bind failed: " << std::strerror(errno) << '\n';
        close(server);
        return 1;
    }

    if (listen(server, 16) < 0) {
        std::cerr << "listen failed: " << std::strerror(errno) << '\n';
        close(server);
        return 1;
    }

    std::cout << "sisterd listening on http://0.0.0.0:" << port
              << " serving " << webRoot << '\n';

    while (keepRunning) {
        fd_set readSet;
        FD_ZERO(&readSet);
        FD_SET(server, &readSet);

        timeval timeout {};
        timeout.tv_sec = 1;
        const int ready = select(server + 1, &readSet, nullptr, nullptr, &timeout);
        if (ready < 0) {
            if (errno == EINTR) continue;
            std::cerr << "select failed: " << std::strerror(errno) << '\n';
            break;
        }
        if (ready == 0) continue;

        sockaddr_in clientAddress {};
        socklen_t clientLength = sizeof(clientAddress);
        const int client = accept(
            server, reinterpret_cast<sockaddr*>(&clientAddress), &clientLength);
        if (client < 0) {
            if (errno == EINTR) continue;
            std::cerr << "accept failed: " << std::strerror(errno) << '\n';
            break;
        }
        handleClient(client, webRoot, auth);
        close(client);
    }

    close(server);
    return 0;
}
