#include "sister_campo_client.hpp"

#include <arpa/inet.h>
#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <netdb.h>
#include <optional>
#include <string>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

namespace sisterd {
namespace {

std::string environment(const char* name, const char* fallback) {
    const char* value = std::getenv(name);
    return value != nullptr && *value != '\0' ? value : fallback;
}

std::optional<std::string> getLocalJson(const std::string& path) {
    const std::string host = environment("SISTER_CAMPO_HOST", "127.0.0.1");
    if (host != "127.0.0.1" && host != "localhost") return std::nullopt;
    const std::string port = environment("SISTER_CAMPO_PORT", "8013");

    addrinfo hints {};
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    addrinfo* addresses = nullptr;
    if (getaddrinfo(host.c_str(), port.c_str(), &hints, &addresses) != 0) {
        return std::nullopt;
    }

    int connection = -1;
    for (auto* address = addresses; address != nullptr; address = address->ai_next) {
        connection = socket(address->ai_family, address->ai_socktype, address->ai_protocol);
        if (connection < 0) continue;
        timeval timeout {.tv_sec = 2, .tv_usec = 0};
        setsockopt(connection, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
        setsockopt(connection, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
        if (connect(connection, address->ai_addr, address->ai_addrlen) == 0) break;
        close(connection);
        connection = -1;
    }
    freeaddrinfo(addresses);
    if (connection < 0) return std::nullopt;

    const std::string request =
        "GET " + path + " HTTP/1.1\r\nHost: " + host +
        "\r\nAccept: application/json\r\nConnection: close\r\n\r\n";
    if (send(connection, request.data(), request.size(), 0) < 0) {
        close(connection);
        return std::nullopt;
    }

    std::string response;
    char buffer[4096];
    while (response.size() < 128 * 1024) {
        const auto received = recv(connection, buffer, sizeof(buffer), 0);
        if (received == 0) break;
        if (received < 0) {
            close(connection);
            return std::nullopt;
        }
        response.append(buffer, static_cast<std::size_t>(received));
    }
    close(connection);

    if (response.rfind("HTTP/1.1 200", 0) != 0) return std::nullopt;
    const auto separator = response.find("\r\n\r\n");
    if (separator == std::string::npos) return std::nullopt;
    return response.substr(separator + 4);
}

} // namespace

std::string sisterCampoIntegrationJson() {
    const auto health = getLocalJson("/api/health");
    const auto capabilities = getLocalJson("/api/capabilities");
    if (!health || !capabilities) {
        return R"({"system_id":"sister_campo","status":"degraded","error":"sister_campo_unavailable"})";
    }
    const bool validHealth =
        health->find(R"("status":"ok")") != std::string::npos &&
        health->find(R"("system_id":"sister_campo")") != std::string::npos;
    const bool validContract =
        capabilities->find(R"("system_id":"sister_campo")") != std::string::npos &&
        capabilities->find(R"("id":"camposync.package")") != std::string::npos &&
        capabilities->find(R"("version":"1.0.0")") != std::string::npos;
    if (!validHealth || !validContract) {
        return R"({"system_id":"sister_campo","status":"degraded","error":"sister_campo_contract_invalid"})";
    }
    return R"({"system_id":"sister_campo","status":"integrated","contract":"camposync.package/1.0.0","channels":["api","offline"],"content_access":"denied_by_default"})";
}

} // namespace sisterd
