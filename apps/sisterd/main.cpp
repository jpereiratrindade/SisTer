#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cerrno>
#include <csignal>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>

namespace {

volatile std::sig_atomic_t keepRunning = 1;

void handleSignal(int) {
    keepRunning = 0;
}

std::string readFile(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        throw std::runtime_error("file not found");
    }
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

std::string httpResponse(int status, std::string_view reason, std::string_view body, std::string_view type) {
    std::ostringstream out;
    out << "HTTP/1.1 " << status << ' ' << reason << "\r\n"
        << "Content-Type: " << type << "\r\n"
        << "Content-Length: " << body.size() << "\r\n"
        << "Connection: close\r\n"
        << "Access-Control-Allow-Origin: *\r\n"
        << "\r\n"
        << body;
    return out.str();
}

std::string jsonHealth() {
    return R"({"status":"ok","service":"sisterd","version":"0.1.0","database":"not_connected"})";
}

std::string jsonContracts() {
    return R"([
  {"name":"System Manifest","version":"0.1.0","required":"Sim"},
  {"name":"CampoSync Package","version":"0.1.0","required":"Para ingestao offline"},
  {"name":"Evidence","version":"0.1.0","required":"Para dado promovido"},
  {"name":"Public Scope","version":"0.1.0","required":"Para classificacao de exposicao"}
])";
}

std::string jsonSystems() {
    return R"([
  {"id":"morfocampo","name":"MorfoCampo","type":"Campo","status":"Operacional","contract":"sister-contracts/0.1.0","access_url":"https://morfocampo.local"},
  {"id":"droneops","name":"DroneOps","type":"Missao","status":"Em validacao","contract":"sister-contracts/0.1.0","access_url":"https://droneops.local"},
  {"id":"camponode","name":"CampoNode","type":"Infraestrutura","status":"Planejado","contract":"sister-contracts/0.1.0","access_url":"https://camponode.local"},
  {"id":"radar_sister_resiliencia","name":"Radar-Sister Resiliencia","type":"Analitico","status":"Operacional","contract":"sister-contracts/0.1.0","access_url":"http://127.0.0.1:8765"},
  {"id":"sister_studio","name":"Sister-Studio","type":"Criativo","status":"Experimental","contract":"sister-contracts/0.1.0","access_url":"https://127.0.0.1:8443"}
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
    return {};
}

std::string sanitizePath(const std::string& rawPath) {
    if (rawPath.empty() || rawPath == "/") return "/index.html";
    if (rawPath.find("..") != std::string::npos) return "/index.html";
    return rawPath;
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

void handleClient(int client, const std::filesystem::path& webRoot) {
    char buffer[8192] = {};
    const ssize_t received = recv(client, buffer, sizeof(buffer) - 1, 0);
    if (received <= 0) return;

    std::istringstream request(std::string(buffer, static_cast<std::size_t>(received)));
    std::string method;
    std::string path;
    request >> method >> path;

    if (method != "GET" && method != "HEAD") {
        sendAll(client, httpResponse(405, "Method Not Allowed", "method not allowed", "text/plain; charset=utf-8"));
        return;
    }

    if (path.rfind("/api/", 0) == 0) {
        const auto body = routeApi(path);
        if (body.empty()) {
            sendAll(client, httpResponse(404, "Not Found", R"({"error":"not_found"})", "application/json; charset=utf-8"));
            return;
        }
        sendAll(client, httpResponse(200, "OK", body, "application/json; charset=utf-8"));
        return;
    }

    const auto safePath = sanitizePath(path);
    const auto filePath = webRoot / safePath.substr(1);
    try {
        const auto body = readFile(filePath);
        sendAll(client, httpResponse(200, "OK", body, contentType(filePath)));
    } catch (const std::exception&) {
        sendAll(client, httpResponse(404, "Not Found", "not found", "text/plain; charset=utf-8"));
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
        timeout.tv_usec = 0;

        const int ready = select(server + 1, &readSet, nullptr, nullptr, &timeout);
        if (ready < 0) {
            if (errno == EINTR) continue;
            std::cerr << "select failed: " << std::strerror(errno) << '\n';
            break;
        }
        if (ready == 0) {
            continue;
        }

        sockaddr_in clientAddress {};
        socklen_t clientLength = sizeof(clientAddress);
        const int client = accept(server, reinterpret_cast<sockaddr*>(&clientAddress), &clientLength);
        if (client < 0) {
            if (errno == EINTR) continue;
            std::cerr << "accept failed: " << std::strerror(errno) << '\n';
            break;
        }
        handleClient(client, webRoot);
        close(client);
    }

    close(server);
    return 0;
}
