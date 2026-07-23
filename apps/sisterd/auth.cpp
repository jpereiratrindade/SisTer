#include "auth.hpp"

#include <openssl/crypto.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/sha.h>

#include <algorithm>
#include <array>
#include <cctype>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace sisterd {
namespace {

constexpr int passwordIterations = 210000;
constexpr std::chrono::hours sessionLifetime{8};

std::string hexEncode(const unsigned char* data, std::size_t size) {
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (std::size_t index = 0; index < size; ++index) {
        out << std::setw(2) << static_cast<unsigned int>(data[index]);
    }
    return out.str();
}

std::vector<unsigned char> hexDecode(const std::string& value) {
    if (value.size() % 2 != 0) return {};
    std::vector<unsigned char> bytes(value.size() / 2);
    for (std::size_t index = 0; index < bytes.size(); ++index) {
        try {
            bytes[index] = static_cast<unsigned char>(
                std::stoul(value.substr(index * 2, 2), nullptr, 16));
        } catch (const std::exception&) {
            return {};
        }
    }
    return bytes;
}

std::string randomHex(std::size_t byteCount) {
    std::vector<unsigned char> bytes(byteCount);
    if (RAND_bytes(bytes.data(), static_cast<int>(bytes.size())) != 1) {
        throw std::runtime_error("secure random generation failed");
    }
    return hexEncode(bytes.data(), bytes.size());
}

std::string sha256(const std::string& value) {
    std::array<unsigned char, SHA256_DIGEST_LENGTH> digest{};
    SHA256(
        reinterpret_cast<const unsigned char*>(value.data()),
        value.size(),
        digest.data());
    return hexEncode(digest.data(), digest.size());
}

std::string passwordHash(const std::string& password, const std::string& saltHex) {
    const auto salt = hexDecode(saltHex);
    std::array<unsigned char, 32> output{};
    if (salt.empty() ||
        PKCS5_PBKDF2_HMAC(
            password.data(),
            static_cast<int>(password.size()),
            salt.data(),
            static_cast<int>(salt.size()),
            passwordIterations,
            EVP_sha256(),
            static_cast<int>(output.size()),
            output.data()) != 1) {
        throw std::runtime_error("password derivation failed");
    }
    return hexEncode(output.data(), output.size());
}

std::string normalizeEmail(std::string email) {
    std::transform(email.begin(), email.end(), email.begin(), [](unsigned char value) {
        return static_cast<char>(std::tolower(value));
    });
    return email;
}

bool validField(const std::string& value) {
    return !value.empty() &&
        value.find('\t') == std::string::npos &&
        value.find('\n') == std::string::npos &&
        value.find('\r') == std::string::npos;
}

} // namespace

AuthStore::AuthStore(std::filesystem::path path) : path_(std::move(path)) {
    load();
}

void AuthStore::load() {
    std::lock_guard lock(mutex_);
    users_.clear();

    std::ifstream input(path_);
    std::string line;
    while (std::getline(input, line)) {
        std::istringstream row(line);
        StoredUser user;
        if (std::getline(row, user.publicUser.id, '\t') &&
            std::getline(row, user.publicUser.name, '\t') &&
            std::getline(row, user.publicUser.email, '\t') &&
            std::getline(row, user.publicUser.role, '\t') &&
            std::getline(row, user.salt, '\t') &&
            std::getline(row, user.passwordHash) &&
            !user.publicUser.id.empty()) {
            users_.push_back(std::move(user));
        }
    }
}

void AuthStore::save() const {
    std::filesystem::create_directories(path_.parent_path());
    const auto temporary = path_.string() + ".tmp";
    {
        std::ofstream output(temporary, std::ios::trunc);
        if (!output) throw std::runtime_error("unable to persist users");
        for (const auto& user : users_) {
            output << user.publicUser.id << '\t'
                   << user.publicUser.name << '\t'
                   << user.publicUser.email << '\t'
                   << user.publicUser.role << '\t'
                   << user.salt << '\t'
                   << user.passwordHash << '\n';
        }
    }
    std::filesystem::permissions(
        temporary,
        std::filesystem::perms::owner_read | std::filesystem::perms::owner_write,
        std::filesystem::perm_options::replace);
    std::filesystem::rename(temporary, path_);
}

bool AuthStore::bootstrapOpen() const {
    std::lock_guard lock(mutex_);
    return users_.empty();
}

AuthResult AuthStore::createSession(const StoredUser& user) {
    const auto token = randomHex(32);
    sessions_[sha256(token)] = {user.publicUser.id, std::chrono::system_clock::now() + sessionLifetime};
    return {user.publicUser, token};
}

std::optional<AuthResult> AuthStore::registerAdmin(
    const std::string& name,
    const std::string& rawEmail,
    const std::string& password) {
    std::lock_guard lock(mutex_);
    const auto email = normalizeEmail(rawEmail);
    if (!users_.empty() || name.size() < 2 || password.size() < 12 ||
        email.find('@') == std::string::npos || !validField(name) || !validField(email)) {
        return std::nullopt;
    }

    StoredUser user;
    user.publicUser = {randomHex(16), name, email, "admin"};
    user.salt = randomHex(16);
    user.passwordHash = passwordHash(password, user.salt);
    users_.push_back(user);
    save();
    return createSession(users_.back());
}

std::optional<AuthResult> AuthStore::login(
    const std::string& rawEmail,
    const std::string& password) {
    std::lock_guard lock(mutex_);
    const auto email = normalizeEmail(rawEmail);
    const auto found = std::find_if(users_.begin(), users_.end(), [&](const StoredUser& user) {
        return user.publicUser.email == email;
    });

    const auto fallbackSalt = std::string(32, '0');
    const auto candidate = passwordHash(password, found == users_.end() ? fallbackSalt : found->salt);
    const auto expected = found == users_.end() ? std::string(64, '0') : found->passwordHash;
    const bool valid = candidate.size() == expected.size() &&
        CRYPTO_memcmp(candidate.data(), expected.data(), candidate.size()) == 0;
    if (!valid || found == users_.end()) return std::nullopt;
    return createSession(*found);
}

std::vector<AuthUser> AuthStore::users() const {
    std::lock_guard lock(mutex_);
    std::vector<AuthUser> result;
    result.reserve(users_.size());
    for (const auto& user : users_) result.push_back(user.publicUser);
    return result;
}

std::optional<AuthUser> AuthStore::createUser(
    const std::string& name,
    const std::string& rawEmail,
    const std::string& password,
    const std::string& role) {
    std::lock_guard lock(mutex_);
    const auto email = normalizeEmail(rawEmail);
    const bool duplicate = std::any_of(users_.begin(), users_.end(), [&](const StoredUser& user) {
        return user.publicUser.email == email;
    });
    if (duplicate || name.size() < 2 || password.size() < 12 ||
        email.find('@') == std::string::npos || (role != "admin" && role != "user") ||
        !validField(name) || !validField(email)) {
        return std::nullopt;
    }

    StoredUser user;
    user.publicUser = {randomHex(16), name, email, role};
    user.salt = randomHex(16);
    user.passwordHash = passwordHash(password, user.salt);
    users_.push_back(user);
    save();
    return users_.back().publicUser;
}

std::optional<AuthUser> AuthStore::userForToken(const std::string& token) {
    if (token.empty()) return std::nullopt;
    std::lock_guard lock(mutex_);
    const auto key = sha256(token);
    const auto session = sessions_.find(key);
    if (session == sessions_.end()) return std::nullopt;
    if (session->second.expiresAt <= std::chrono::system_clock::now()) {
        sessions_.erase(session);
        return std::nullopt;
    }
    const auto user = std::find_if(users_.begin(), users_.end(), [&](const StoredUser& item) {
        return item.publicUser.id == session->second.userId;
    });
    return user == users_.end() ? std::nullopt : std::optional<AuthUser>{user->publicUser};
}

void AuthStore::logout(const std::string& token) {
    if (token.empty()) return;
    std::lock_guard lock(mutex_);
    sessions_.erase(sha256(token));
}

} // namespace sisterd
