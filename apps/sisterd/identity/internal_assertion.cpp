#include "internal_assertion.hpp"

#include <openssl/evp.h>
#include <openssl/pem.h>
#include <openssl/rand.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <charconv>
#include <fstream>
#include <limits>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <system_error>

namespace sisterd::identity {
namespace {

constexpr std::size_t kMaximumKeyBytes = 64 * 1024;
constexpr std::size_t kMaximumAssertionBytes = 16 * 1024;

using BioPtr = std::unique_ptr<BIO, decltype(&BIO_free)>;
using KeyPtr = std::unique_ptr<EVP_PKEY, decltype(&EVP_PKEY_free)>;
using MdContextPtr = std::unique_ptr<EVP_MD_CTX, decltype(&EVP_MD_CTX_free)>;

bool validKid(std::string_view value) {
    return !value.empty() && value.size() <= 64 &&
        std::all_of(value.begin(), value.end(), [](unsigned char character) {
            return std::isalnum(character) || character == '.' || character == '_' || character == '-';
        });
}

bool validToken(std::string_view value, std::size_t minimum, std::size_t maximum) {
    return value.size() >= minimum && value.size() <= maximum &&
        std::all_of(value.begin(), value.end(), [](unsigned char character) {
            return std::isalnum(character) || character == '.' || character == '_' ||
                   character == '-' || character == ':';
        });
}

bool validCapability(std::string_view value) {
    if (value.empty() || value.size() > 120) return false;
    std::size_t dots = 0;
    bool segmentStart = true;
    for (const unsigned char character : value) {
        if (character == '.') {
            if (segmentStart) return false;
            ++dots;
            segmentStart = true;
        } else {
            if (segmentStart && !std::islower(character)) return false;
            if (!std::islower(character) && !std::isdigit(character) && character != '_') return false;
            segmentStart = false;
        }
    }
    return dots == 2 && !segmentStart;
}

std::string jsonEscape(std::string_view value) {
    std::ostringstream output;
    for (const unsigned char character : value) {
        switch (character) {
            case '"': output << "\\\""; break;
            case '\\': output << "\\\\"; break;
            case '\b': output << "\\b"; break;
            case '\f': output << "\\f"; break;
            case '\n': output << "\\n"; break;
            case '\r': output << "\\r"; break;
            case '\t': output << "\\t"; break;
            default:
                if (character < 0x20 || character > 0x7e) {
                    throw std::runtime_error("assertion claims must contain printable ASCII");
                }
                output << static_cast<char>(character);
        }
    }
    return output.str();
}

std::string serializeClaims(const InternalAssertionClaims& claims) {
    if (claims.issuer != "sisterd" || !validToken(claims.subject, 1, 120) ||
        !validToken(claims.audience, 3, 64) || !validToken(claims.purpose, 3, 120) ||
        !validToken(claims.jti, 16, 120) || !validToken(claims.requestId, 16, 128) ||
        claims.capabilities.empty() || claims.capabilities.size() > 8 ||
        claims.issuedAt < 0 || claims.expiresAt <= claims.issuedAt) {
        throw std::runtime_error("invalid internal assertion claims");
    }
    if (!std::all_of(claims.capabilities.begin(), claims.capabilities.end(), validCapability)) {
        throw std::runtime_error("invalid internal assertion capability");
    }

    std::ostringstream output;
    output << "{\"iss\":\"sisterd\",\"sub\":\"" << jsonEscape(claims.subject)
           << "\",\"aud\":\"" << jsonEscape(claims.audience) << "\",\"capabilities\":[";
    for (std::size_t index = 0; index < claims.capabilities.size(); ++index) {
        if (index != 0) output << ',';
        output << '"' << jsonEscape(claims.capabilities[index]) << '"';
    }
    output << "],\"purpose\":\"" << jsonEscape(claims.purpose)
           << "\",\"iat\":" << claims.issuedAt
           << ",\"exp\":" << claims.expiresAt
           << ",\"jti\":\"" << jsonEscape(claims.jti)
           << "\",\"request_id\":\"" << jsonEscape(claims.requestId) << "\"}";
    return output.str();
}

std::string base64UrlEncode(const unsigned char* data, std::size_t size) {
    if (size > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
        throw std::runtime_error("value too large to encode");
    }
    std::string encoded(4 * ((size + 2) / 3), '\0');
    const int count = EVP_EncodeBlock(
        reinterpret_cast<unsigned char*>(encoded.data()), data, static_cast<int>(size));
    if (count < 0) throw std::runtime_error("base64 encoding failed");
    encoded.resize(static_cast<std::size_t>(count));
    while (!encoded.empty() && encoded.back() == '=') encoded.pop_back();
    std::replace(encoded.begin(), encoded.end(), '+', '-');
    std::replace(encoded.begin(), encoded.end(), '/', '_');
    return encoded;
}

std::string base64UrlEncode(std::string_view value) {
    return base64UrlEncode(reinterpret_cast<const unsigned char*>(value.data()), value.size());
}

std::optional<std::string> base64UrlDecode(std::string_view value) {
    if (value.empty() || value.size() > kMaximumAssertionBytes || value.size() % 4 == 1) {
        return std::nullopt;
    }
    std::string padded(value);
    for (char& character : padded) {
        if (character == '-') character = '+';
        else if (character == '_') character = '/';
        else if (!std::isalnum(static_cast<unsigned char>(character)) && character != '+' && character != '/') {
            return std::nullopt;
        }
    }
    while (padded.size() % 4 != 0) padded.push_back('=');
    std::string decoded((padded.size() / 4) * 3, '\0');
    const int count = EVP_DecodeBlock(
        reinterpret_cast<unsigned char*>(decoded.data()),
        reinterpret_cast<const unsigned char*>(padded.data()),
        static_cast<int>(padded.size()));
    if (count < 0) return std::nullopt;
    std::size_t decodedSize = static_cast<std::size_t>(count);
    if (!padded.empty() && padded.back() == '=') --decodedSize;
    if (padded.size() >= 2 && padded[padded.size() - 2] == '=') --decodedSize;
    decoded.resize(decodedSize);
    return decoded;
}

std::string readFile(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("cannot read internal identity key file");
    std::string value((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    if (value.empty() || value.size() > kMaximumKeyBytes) {
        throw std::runtime_error("invalid internal identity key file size");
    }
    return value;
}

KeyPtr privateKey(std::string_view pem) {
    BioPtr bio(BIO_new_mem_buf(pem.data(), static_cast<int>(pem.size())), BIO_free);
    if (!bio) throw std::runtime_error("cannot allocate private key reader");
    KeyPtr key(PEM_read_bio_PrivateKey(bio.get(), nullptr, nullptr, nullptr), EVP_PKEY_free);
    if (!key || EVP_PKEY_base_id(key.get()) != EVP_PKEY_ED25519) {
        throw std::runtime_error("internal identity private key must be Ed25519 PEM");
    }
    return key;
}

KeyPtr publicKey(std::string_view pem) {
    BioPtr bio(BIO_new_mem_buf(pem.data(), static_cast<int>(pem.size())), BIO_free);
    if (!bio) throw std::runtime_error("cannot allocate public key reader");
    KeyPtr key(PEM_read_bio_PUBKEY(bio.get(), nullptr, nullptr, nullptr), EVP_PKEY_free);
    if (!key || EVP_PKEY_base_id(key.get()) != EVP_PKEY_ED25519) {
        throw std::runtime_error("internal identity public key must be Ed25519 PEM");
    }
    return key;
}

class JsonReader {
public:
    explicit JsonReader(std::string_view input) : input_(input) {}

    void objectStart() { whitespace(); expect('{'); }
    bool objectEnd() { whitespace(); return consume('}'); }
    void arrayStart() { whitespace(); expect('['); }
    bool arrayEnd() { whitespace(); return consume(']'); }
    void comma() { whitespace(); expect(','); }
    void colon() { whitespace(); expect(':'); }

    std::string string() {
        whitespace();
        expect('"');
        std::string output;
        while (position_ < input_.size()) {
            const char character = input_[position_++];
            if (character == '"') return output;
            if (static_cast<unsigned char>(character) < 0x20) fail();
            if (character != '\\') {
                output.push_back(character);
                continue;
            }
            if (position_ >= input_.size()) fail();
            switch (input_[position_++]) {
                case '"': output.push_back('"'); break;
                case '\\': output.push_back('\\'); break;
                case '/': output.push_back('/'); break;
                case 'b': output.push_back('\b'); break;
                case 'f': output.push_back('\f'); break;
                case 'n': output.push_back('\n'); break;
                case 'r': output.push_back('\r'); break;
                case 't': output.push_back('\t'); break;
                default: fail();
            }
        }
        fail();
    }

    std::int64_t integer() {
        whitespace();
        const auto start = position_;
        if (position_ < input_.size() && input_[position_] == '-') ++position_;
        while (position_ < input_.size() && std::isdigit(static_cast<unsigned char>(input_[position_]))) {
            ++position_;
        }
        if (position_ == start || (position_ == start + 1 && input_[start] == '-')) fail();
        std::int64_t value{};
        const auto [pointer, error] = std::from_chars(
            input_.data() + start, input_.data() + position_, value);
        if (error != std::errc{} || pointer != input_.data() + position_) fail();
        return value;
    }

    bool done() { whitespace(); return position_ == input_.size(); }

private:
    [[noreturn]] void fail() const { throw std::runtime_error("invalid assertion JSON"); }
    void whitespace() {
        while (position_ < input_.size() &&
               std::isspace(static_cast<unsigned char>(input_[position_]))) ++position_;
    }
    bool consume(char expected) {
        if (position_ < input_.size() && input_[position_] == expected) {
            ++position_;
            return true;
        }
        return false;
    }
    void expect(char expected) { if (!consume(expected)) fail(); }

    std::string_view input_;
    std::size_t position_ = 0;
};

struct Header {
    std::string alg;
    std::string typ;
    std::string kid;
};

Header parseHeader(std::string_view json) {
    JsonReader reader(json);
    Header header;
    bool alg = false, typ = false, kid = false;
    reader.objectStart();
    bool first = true;
    while (!reader.objectEnd()) {
        if (!first) reader.comma();
        first = false;
        const auto name = reader.string();
        reader.colon();
        if (name == "alg" && !alg) { header.alg = reader.string(); alg = true; }
        else if (name == "typ" && !typ) { header.typ = reader.string(); typ = true; }
        else if (name == "kid" && !kid) { header.kid = reader.string(); kid = true; }
        else throw std::runtime_error("invalid assertion header");
    }
    if (!reader.done() || !alg || !typ || !kid || header.alg != "EdDSA" ||
        header.typ != "sister-internal+jwt" || !validKid(header.kid)) {
        throw std::runtime_error("invalid assertion header");
    }
    return header;
}

InternalAssertionClaims parseClaims(std::string_view json) {
    JsonReader reader(json);
    InternalAssertionClaims claims;
    bool iss = false, sub = false, aud = false, capabilities = false, purpose = false;
    bool iat = false, exp = false, jti = false, requestId = false;
    reader.objectStart();
    bool first = true;
    while (!reader.objectEnd()) {
        if (!first) reader.comma();
        first = false;
        const auto name = reader.string();
        reader.colon();
        if (name == "iss" && !iss) { claims.issuer = reader.string(); iss = true; }
        else if (name == "sub" && !sub) { claims.subject = reader.string(); sub = true; }
        else if (name == "aud" && !aud) { claims.audience = reader.string(); aud = true; }
        else if (name == "purpose" && !purpose) { claims.purpose = reader.string(); purpose = true; }
        else if (name == "iat" && !iat) { claims.issuedAt = reader.integer(); iat = true; }
        else if (name == "exp" && !exp) { claims.expiresAt = reader.integer(); exp = true; }
        else if (name == "jti" && !jti) { claims.jti = reader.string(); jti = true; }
        else if (name == "request_id" && !requestId) {
            claims.requestId = reader.string(); requestId = true;
        } else if (name == "capabilities" && !capabilities) {
            capabilities = true;
            reader.arrayStart();
            bool firstCapability = true;
            while (!reader.arrayEnd()) {
                if (!firstCapability) reader.comma();
                firstCapability = false;
                claims.capabilities.push_back(reader.string());
                if (claims.capabilities.size() > 8) throw std::runtime_error("too many capabilities");
            }
        } else {
            throw std::runtime_error("unknown or duplicate assertion claim");
        }
    }
    if (!reader.done() || !iss || !sub || !aud || !capabilities || !purpose || !iat || !exp ||
        !jti || !requestId) {
        throw std::runtime_error("missing assertion claim");
    }
    (void)serializeClaims(claims);
    return claims;
}

VerificationResult failure(std::string error) {
    return {false, std::move(error), {}};
}

} // namespace

FileKeyProvider::FileKeyProvider(std::filesystem::path privateKeyPath, std::string kid)
    : privateKeyPath_(std::move(privateKeyPath)), kid_(std::move(kid)) {
    if (!privateKeyPath_.is_absolute()) {
        throw std::runtime_error("internal identity private key path must be absolute");
    }
    if (!validKid(kid_)) throw std::runtime_error("invalid internal identity key id");
}

SigningKey FileKeyProvider::currentSigningKey() const {
    if (!std::filesystem::is_regular_file(privateKeyPath_)) {
        throw std::runtime_error("internal identity private key must be a regular file");
    }
    const auto permissions = std::filesystem::status(privateKeyPath_).permissions();
    using Perms = std::filesystem::perms;
    if ((permissions & (Perms::group_all | Perms::others_all)) != Perms::none) {
        throw std::runtime_error("internal identity private key permissions must be 0600 or stricter");
    }
    auto pem = readFile(privateKeyPath_);
    (void)privateKey(pem);
    return {kid_, std::move(pem)};
}

AssertionSigner::AssertionSigner(std::shared_ptr<const KeyProvider> keyProvider)
    : keyProvider_(std::move(keyProvider)) {
    if (!keyProvider_) throw std::runtime_error("internal identity key provider is required");
}

std::string AssertionSigner::sign(const InternalAssertionClaims& claims) const {
    const auto signingKey = keyProvider_->currentSigningKey();
    if (!validKid(signingKey.kid)) throw std::runtime_error("invalid internal identity key id");
    auto key = privateKey(signingKey.privateKeyPem);
    const std::string header = "{\"alg\":\"EdDSA\",\"typ\":\"sister-internal+jwt\",\"kid\":\"" +
        jsonEscape(signingKey.kid) + "\"}";
    const auto payload = serializeClaims(claims);
    const auto signingInput = base64UrlEncode(header) + "." + base64UrlEncode(payload);

    MdContextPtr context(EVP_MD_CTX_new(), EVP_MD_CTX_free);
    if (!context || EVP_DigestSignInit(context.get(), nullptr, nullptr, nullptr, key.get()) != 1) {
        throw std::runtime_error("cannot initialize internal assertion signature");
    }
    std::array<unsigned char, 64> signature{};
    std::size_t signatureSize = signature.size();
    if (EVP_DigestSign(
            context.get(), signature.data(), &signatureSize,
            reinterpret_cast<const unsigned char*>(signingInput.data()), signingInput.size()) != 1) {
        throw std::runtime_error("cannot sign internal assertion");
    }
    return signingInput + "." + base64UrlEncode(signature.data(), signatureSize);
}

AssertionVerifier::AssertionVerifier(AssertionVerifier&& other) noexcept {
    std::lock_guard lock(other.replayMutex_);
    publicKeys_ = std::move(other.publicKeys_);
    seenJtis_ = std::move(other.seenJtis_);
}

void AssertionVerifier::addPublicKey(std::string kid, std::string publicKeyPem) {
    if (!validKid(kid)) throw std::runtime_error("invalid internal identity key id");
    (void)publicKey(publicKeyPem);
    publicKeys_.insert_or_assign(std::move(kid), std::move(publicKeyPem));
}

void AssertionVerifier::addPublicKeyFile(
    std::string kid, const std::filesystem::path& publicKeyPath) {
    if (!publicKeyPath.is_absolute()) {
        throw std::runtime_error("internal identity public key path must be absolute");
    }
    addPublicKey(std::move(kid), readFile(publicKeyPath));
}

VerificationResult AssertionVerifier::verify(
    std::string_view compactAssertion,
    const VerificationRequirements& requirements,
    std::chrono::system_clock::time_point now) {
    try {
        if (compactAssertion.empty() || compactAssertion.size() > kMaximumAssertionBytes) {
            return failure("malformed_assertion");
        }
        const auto firstDot = compactAssertion.find('.');
        const auto secondDot = firstDot == std::string_view::npos
            ? std::string_view::npos : compactAssertion.find('.', firstDot + 1);
        if (firstDot == std::string_view::npos || secondDot == std::string_view::npos ||
            compactAssertion.find('.', secondDot + 1) != std::string_view::npos) {
            return failure("malformed_assertion");
        }

        const auto decodedHeader = base64UrlDecode(compactAssertion.substr(0, firstDot));
        const auto decodedPayload = base64UrlDecode(
            compactAssertion.substr(firstDot + 1, secondDot - firstDot - 1));
        const auto signature = base64UrlDecode(compactAssertion.substr(secondDot + 1));
        if (!decodedHeader || !decodedPayload || !signature || signature->size() != 64) {
            return failure("malformed_assertion");
        }

        const auto header = parseHeader(*decodedHeader);
        const auto foundKey = publicKeys_.find(header.kid);
        if (foundKey == publicKeys_.end()) return failure("unknown_key");
        auto key = publicKey(foundKey->second);
        MdContextPtr context(EVP_MD_CTX_new(), EVP_MD_CTX_free);
        if (!context || EVP_DigestVerifyInit(context.get(), nullptr, nullptr, nullptr, key.get()) != 1) {
            return failure("verification_failure");
        }
        const auto signingInput = compactAssertion.substr(0, secondDot);
        if (EVP_DigestVerify(
                context.get(), reinterpret_cast<const unsigned char*>(signature->data()), signature->size(),
                reinterpret_cast<const unsigned char*>(signingInput.data()), signingInput.size()) != 1) {
            return failure("invalid_signature");
        }

        auto claims = parseClaims(*decodedPayload);
        const auto nowSeconds = std::chrono::duration_cast<std::chrono::seconds>(
            now.time_since_epoch()).count();
        if (claims.issuer != "sisterd") return failure("invalid_issuer");
        if (claims.audience != requirements.audience) return failure("invalid_audience");
        if (claims.purpose != requirements.purpose) return failure("invalid_purpose");
        if (std::find(claims.capabilities.begin(), claims.capabilities.end(), requirements.capability) ==
            claims.capabilities.end()) return failure("capability_missing");
        if (claims.issuedAt > nowSeconds + requirements.clockSkew.count()) {
            return failure("issued_in_future");
        }
        if (claims.expiresAt <= nowSeconds - requirements.clockSkew.count()) {
            return failure("assertion_expired");
        }
        if (claims.expiresAt - claims.issuedAt > requirements.maximumLifetime.count()) {
            return failure("lifetime_exceeded");
        }

        {
            std::lock_guard lock(replayMutex_);
            for (auto iterator = seenJtis_.begin(); iterator != seenJtis_.end();) {
                if (iterator->second <= nowSeconds - requirements.clockSkew.count()) {
                    iterator = seenJtis_.erase(iterator);
                } else {
                    ++iterator;
                }
            }
            if (seenJtis_.contains(claims.jti)) return failure("assertion_replayed");
            seenJtis_.emplace(claims.jti, claims.expiresAt);
        }
        return {true, {}, std::move(claims)};
    } catch (const std::exception&) {
        return failure("malformed_assertion");
    }
}

std::string randomAssertionId(std::size_t bytes) {
    if (bytes < 8 || bytes > 60) throw std::runtime_error("invalid assertion id size");
    std::vector<unsigned char> random(bytes);
    if (RAND_bytes(random.data(), static_cast<int>(random.size())) != 1) {
        throw std::runtime_error("cannot generate assertion id");
    }
    static constexpr char hexadecimal[] = "0123456789abcdef";
    std::string output;
    output.reserve(bytes * 2);
    for (const unsigned char value : random) {
        output.push_back(hexadecimal[value >> 4]);
        output.push_back(hexadecimal[value & 0x0f]);
    }
    return output;
}

} // namespace sisterd::identity
