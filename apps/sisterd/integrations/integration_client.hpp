#pragma once

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <string>

namespace sisterd::integrations {

struct AuthorizedIntegrationRequest {
    std::string method;
    std::string path;
    std::string query;
    std::string contentType;
    std::string accept;
    std::string body;
    std::string subject;
    std::string capability;
    std::string purpose;
    std::string requestId;
};

struct IntegrationClientConfig {
    std::uint16_t port = 0;
    int timeoutMilliseconds = 5'000;
    std::filesystem::path privateKeyFile;
    std::string keyId;
    std::chrono::seconds assertionTtl{60};
};

class IntegrationClient {
public:
    virtual ~IntegrationClient() = default;
    [[nodiscard]] virtual std::string execute(const AuthorizedIntegrationRequest& request) const = 0;
};

} // namespace sisterd::integrations
