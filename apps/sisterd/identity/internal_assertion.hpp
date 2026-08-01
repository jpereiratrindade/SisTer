#pragma once

#include "key_provider.hpp"

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <mutex>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace sisterd::identity {

struct InternalAssertionClaims {
    std::string issuer = "sisterd";
    std::string subject;
    std::string audience;
    std::vector<std::string> capabilities;
    std::string purpose;
    std::int64_t issuedAt = 0;
    std::int64_t expiresAt = 0;
    std::string jti;
    std::string requestId;
};

class AssertionSigner {
public:
    explicit AssertionSigner(std::shared_ptr<const KeyProvider> keyProvider);
    [[nodiscard]] std::string sign(const InternalAssertionClaims& claims) const;

private:
    std::shared_ptr<const KeyProvider> keyProvider_;
};

struct VerificationRequirements {
    std::string audience;
    std::string capability;
    std::string purpose;
    std::chrono::seconds clockSkew{5};
    std::chrono::seconds maximumLifetime{300};
};

struct VerificationResult {
    bool valid = false;
    std::string error;
    InternalAssertionClaims claims;
};

class AssertionVerifier {
public:
    AssertionVerifier() = default;
    AssertionVerifier(const AssertionVerifier&) = delete;
    AssertionVerifier& operator=(const AssertionVerifier&) = delete;
    AssertionVerifier(AssertionVerifier&& other) noexcept;

    void addPublicKey(std::string kid, std::string publicKeyPem);
    void addPublicKeyFile(std::string kid, const std::filesystem::path& publicKeyPath);

    [[nodiscard]] VerificationResult verify(
        std::string_view compactAssertion,
        const VerificationRequirements& requirements,
        std::chrono::system_clock::time_point now = std::chrono::system_clock::now());

private:
    std::unordered_map<std::string, std::string> publicKeys_;
    std::unordered_map<std::string, std::int64_t> seenJtis_;
    std::mutex replayMutex_;
};

[[nodiscard]] std::string randomAssertionId(std::size_t bytes = 16);

} // namespace sisterd::identity
