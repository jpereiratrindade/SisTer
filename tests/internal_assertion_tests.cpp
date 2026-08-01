#include "internal_assertion.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

constexpr std::string_view kPrivateKey = R"(-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIIUfIgspmWAUj39fzrFNyE12Q4sfpRfjS3NiIiVC/LOn
-----END PRIVATE KEY-----
)";

constexpr std::string_view kPublicKey = R"(-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAzUnUCnCF15ZpU/SEX0AV1x2TEH/DaCbMYuChuIYyWik=
-----END PUBLIC KEY-----
)";

constexpr std::string_view kOtherPublicKey = R"(-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAHNJFXQITeV8+sJmzqN+JuxEYk5s8mADWdDAkvRFMeRo=
-----END PUBLIC KEY-----
)";

void expect(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

sisterd::identity::InternalAssertionClaims claimsAt(std::int64_t now, std::string jti) {
    return {
        "sisterd",
        "123e4567-e89b-12d3-a456-426614174000",
        "sister_nexo",
        {"nexo.projects.read"},
        "research_operations",
        now,
        now + 60,
        std::move(jti),
        "0123456789abcdef",
    };
}

sisterd::identity::VerificationRequirements requirements() {
    return {"sister_nexo", "nexo.projects.read", "research_operations"};
}

sisterd::identity::AssertionVerifier verifier() {
    sisterd::identity::AssertionVerifier value;
    value.addPublicKey("identity-2026-08", std::string(kPublicKey));
    return value;
}

} // namespace

int main() {
    const auto suffix = std::to_string(
        std::chrono::steady_clock::now().time_since_epoch().count());
    const auto keyFile = std::filesystem::temp_directory_path() /
        ("sister-internal-identity-" + suffix + ".pem");
    {
        std::ofstream output(keyFile, std::ios::binary | std::ios::trunc);
        output << kPrivateKey;
    }
    std::filesystem::permissions(
        keyFile, std::filesystem::perms::owner_read | std::filesystem::perms::owner_write,
        std::filesystem::perm_options::replace);

    try {
        bool relativePathRejected = false;
        try {
            (void)sisterd::identity::FileKeyProvider(
                "relative-identity-key.pem", "identity-2026-08");
        } catch (const std::exception&) {
            relativePathRejected = true;
        }
        expect(relativePathRejected, "relative private key path must fail closed");

        const auto randomIdA = sisterd::identity::randomAssertionId();
        const auto randomIdB = sisterd::identity::randomAssertionId();
        expect(randomIdA.size() == 32 && randomIdB.size() == 32,
               "random jti must contain 16 bytes encoded as hexadecimal");
        expect(randomIdA != randomIdB, "random jti values must be unique");

        auto provider = std::make_shared<sisterd::identity::FileKeyProvider>(
            keyFile, "identity-2026-08");
        sisterd::identity::AssertionSigner signer(provider);
        const auto nowPoint = std::chrono::system_clock::now();
        const auto now = std::chrono::duration_cast<std::chrono::seconds>(
            nowPoint.time_since_epoch()).count();

        const auto assertion = signer.sign(claimsAt(now, "00000000000000000000000000000001"));
        auto validVerifier = verifier();
        const auto valid = validVerifier.verify(assertion, requirements(), nowPoint);
        expect(valid.valid, "valid signature should be accepted: " + valid.error);
        expect(valid.claims.requestId == "0123456789abcdef", "request_id must be preserved");
        expect(valid.claims.capabilities.size() == 1, "assertion must carry one capability");

        auto tampered = assertion;
        const auto signatureStart = tampered.rfind('.') + 1;
        tampered[signatureStart] = tampered[signatureStart] == 'A' ? 'B' : 'A';
        auto tamperVerifier = verifier();
        expect(
            tamperVerifier.verify(tampered, requirements(), nowPoint).error == "invalid_signature",
            "tampered signature must be rejected");

        sisterd::identity::AssertionVerifier unknownKeyVerifier;
        unknownKeyVerifier.addPublicKey("other-key", std::string(kOtherPublicKey));
        expect(
            unknownKeyVerifier.verify(assertion, requirements(), nowPoint).error == "unknown_key",
            "unknown kid must be rejected");

        auto wrongAudience = requirements();
        wrongAudience.audience = "sister_clima";
        auto audienceVerifier = verifier();
        expect(
            audienceVerifier.verify(assertion, wrongAudience, nowPoint).error == "invalid_audience",
            "wrong audience must be rejected");

        auto expiredClaims = claimsAt(now - 120, "00000000000000000000000000000002");
        expiredClaims.expiresAt = now - 60;
        auto expiryVerifier = verifier();
        expect(
            expiryVerifier.verify(signer.sign(expiredClaims), requirements(), nowPoint).error ==
                "assertion_expired",
            "expired assertion must be rejected");

        auto missingCapability = claimsAt(now, "00000000000000000000000000000003");
        missingCapability.capabilities = {"nexo.evidence.read"};
        auto capabilityVerifier = verifier();
        expect(
            capabilityVerifier.verify(
                signer.sign(missingCapability), requirements(), nowPoint).error ==
                "capability_missing",
            "missing capability must be rejected");

        auto wrongPurpose = requirements();
        wrongPurpose.purpose = "commercial_operations";
        auto purposeVerifier = verifier();
        expect(
            purposeVerifier.verify(assertion, wrongPurpose, nowPoint).error == "invalid_purpose",
            "wrong purpose must be rejected");

        auto futureClaims = claimsAt(now + 60, "00000000000000000000000000000006");
        auto futureVerifier = verifier();
        expect(
            futureVerifier.verify(signer.sign(futureClaims), requirements(), nowPoint).error ==
                "issued_in_future",
            "future iat must be rejected");

        auto excessiveLifetime = claimsAt(now, "00000000000000000000000000000007");
        excessiveLifetime.expiresAt = now + 301;
        auto lifetimeVerifier = verifier();
        expect(
            lifetimeVerifier.verify(
                signer.sign(excessiveLifetime), requirements(), nowPoint).error ==
                "lifetime_exceeded",
            "lifetime above 300 seconds must be rejected");

        auto replayVerifier = verifier();
        const auto replayAssertion = signer.sign(
            claimsAt(now, "00000000000000000000000000000004"));
        expect(replayVerifier.verify(replayAssertion, requirements(), nowPoint).valid,
               "first jti use must pass");
        expect(
            replayVerifier.verify(replayAssertion, requirements(), nowPoint).error ==
                "assertion_replayed",
            "reused jti must be rejected");

        bool insecurePermissionsRejected = false;
        std::filesystem::permissions(
            keyFile, std::filesystem::perms::owner_read | std::filesystem::perms::owner_write |
                std::filesystem::perms::group_read,
            std::filesystem::perm_options::replace);
        try {
            (void)signer.sign(claimsAt(now, "00000000000000000000000000000005"));
        } catch (const std::exception&) {
            insecurePermissionsRejected = true;
        }
        expect(insecurePermissionsRejected, "insecure private key permissions must fail closed");
    } catch (...) {
        std::filesystem::remove(keyFile);
        throw;
    }
    std::filesystem::remove(keyFile);
    std::cout << "internal_assertion_tests ok\n";
    return 0;
}
