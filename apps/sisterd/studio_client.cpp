#include "studio_client.hpp"

#include <arpa/inet.h>
#include <netdb.h>
#include <openssl/ssl.h>
#include <openssl/x509_vfy.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>

namespace sisterd {
namespace {

constexpr std::size_t maximumResponseSize = 128 * 1024;

struct Configuration {
    std::string host{"127.0.0.1"};
    std::string port{"8443"};
    std::string token;
    std::string caFile;
};

struct Result {
    bool success{false};
    std::string body;
    std::string errorCode;
};

std::string environment(std::string_view name) {
    const auto* value = std::getenv(std::string(name).c_str());
    return value == nullptr ? std::string{} : std::string(value);
}

std::string firstLine(const std::filesystem::path& path) {
    std::ifstream input(path);
    std::string value;
    std::getline(input, value);
    while (!value.empty() && (value.back() == '\r' || value.back() == '\n' ||
                              value.back() == ' ' || value.back() == '\t')) {
        value.pop_back();
    }
    return value;
}

std::optional<Configuration> configuration() {
    const auto tokenFile = environment("SISTER_STUDIO_TOKEN_FILE");
    const auto caFile = environment("SISTER_STUDIO_CA_FILE");
    if (tokenFile.empty() || caFile.empty()) return std::nullopt;

    Configuration config;
    config.token = firstLine(tokenFile);
    config.caFile = caFile;
    const auto host = environment("SISTER_STUDIO_HOST");
    const auto port = environment("SISTER_STUDIO_PORT");
    if (!host.empty()) config.host = host;
    if (!port.empty()) config.port = port;
    if (config.token.size() < 32 || !std::filesystem::is_regular_file(config.caFile)) {
        return std::nullopt;
    }
    return config;
}

int connectSocket(const Configuration& config) {
    addrinfo hints{};
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    addrinfo* addresses = nullptr;
    if (getaddrinfo(config.host.c_str(), config.port.c_str(), &hints, &addresses) != 0) {
        return -1;
    }

    int connected = -1;
    for (auto* current = addresses; current != nullptr; current = current->ai_next) {
        const int candidate = socket(current->ai_family, current->ai_socktype, current->ai_protocol);
        if (candidate < 0) continue;
        timeval timeout{};
        timeout.tv_sec = 3;
        setsockopt(candidate, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
        setsockopt(candidate, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
        if (connect(candidate, current->ai_addr, current->ai_addrlen) == 0) {
            connected = candidate;
            break;
        }
        close(candidate);
    }
    freeaddrinfo(addresses);
    return connected;
}

bool isIpAddress(const std::string& host) {
    in_addr ipv4{};
    in6_addr ipv6{};
    return inet_pton(AF_INET, host.c_str(), &ipv4) == 1 ||
           inet_pton(AF_INET6, host.c_str(), &ipv6) == 1;
}

Result fetch(const Configuration& config, std::string_view path) {
    SSL_CTX* context = SSL_CTX_new(TLS_client_method());
    if (context == nullptr) return {false, {}, "tls_initialization_failed"};
    SSL_CTX_set_min_proto_version(context, TLS1_2_VERSION);
    SSL_CTX_set_verify(context, SSL_VERIFY_PEER, nullptr);
    if (SSL_CTX_load_verify_locations(context, config.caFile.c_str(), nullptr) != 1) {
        SSL_CTX_free(context);
        return {false, {}, "trust_configuration_failed"};
    }

    const int socketFd = connectSocket(config);
    if (socketFd < 0) {
        SSL_CTX_free(context);
        return {false, {}, "studio_unavailable"};
    }

    SSL* ssl = SSL_new(context);
    SSL_set_fd(ssl, socketFd);
    auto* verify = SSL_get0_param(ssl);
    if (isIpAddress(config.host)) {
        X509_VERIFY_PARAM_set1_ip_asc(verify, config.host.c_str());
    } else {
        SSL_set_tlsext_host_name(ssl, config.host.c_str());
        X509_VERIFY_PARAM_set1_host(verify, config.host.c_str(), 0);
    }
    if (SSL_connect(ssl) != 1 || SSL_get_verify_result(ssl) != X509_V_OK) {
        SSL_free(ssl);
        close(socketFd);
        SSL_CTX_free(context);
        return {false, {}, "studio_identity_not_verified"};
    }

    const auto request = "GET " + std::string(path) + " HTTP/1.1\r\nHost: " + config.host +
                         "\r\nAuthorization: Bearer " + config.token +
                         "\r\nAccept: application/json\r\nConnection: close\r\n\r\n";
    std::size_t sent = 0;
    while (sent < request.size()) {
        const int count = SSL_write(ssl, request.data() + sent,
                                    static_cast<int>(request.size() - sent));
        if (count <= 0) break;
        sent += static_cast<std::size_t>(count);
    }

    std::string response;
    char buffer[8192];
    while (sent == request.size() && response.size() < maximumResponseSize) {
        const int count = SSL_read(ssl, buffer, sizeof(buffer));
        if (count <= 0) break;
        response.append(buffer, static_cast<std::size_t>(count));
    }
    SSL_shutdown(ssl);
    SSL_free(ssl);
    close(socketFd);
    SSL_CTX_free(context);

    const auto headerEnd = response.find("\r\n\r\n");
    const bool successStatus = response.rfind("HTTP/1.1 200 ", 0) == 0 ||
                               response.rfind("HTTP/1.0 200 ", 0) == 0;
    if (!successStatus || headerEnd == std::string::npos) {
        return {false, {}, "studio_contract_request_failed"};
    }
    auto body = response.substr(headerEnd + 4);
    const bool jsonObject = !body.empty() && body.front() == '{' && body.back() == '}';
    const bool expectedContract =
        body.find(R"("contract_id":"sister-studio.integration")") != std::string::npos &&
        body.find(R"("contract_version":"1.0.0")") != std::string::npos;
    if (!jsonObject || !expectedContract) {
        return {false, {}, "studio_contract_invalid"};
    }
    return {true, std::move(body), {}};
}

std::string error(std::string_view code) {
    return "{\"status\":\"unavailable\",\"error_code\":\"" + std::string(code) + "\"}";
}

} // namespace

std::string sisterStudioIntegrationJson() {
    const auto config = configuration();
    if (!config) {
        return R"({"status":"not_configured","error_code":"integration_configuration_unavailable"})";
    }
    const auto capabilities = fetch(*config, "/api/sister/v1/capabilities");
    if (!capabilities.success) return error(capabilities.errorCode);
    const auto health = fetch(*config, "/api/sister/v1/health");
    if (!health.success) return error(health.errorCode);
    return "{\"status\":\"connected\",\"capabilities\":" + capabilities.body +
           ",\"health\":" + health.body + "}";
}

} // namespace sisterd
