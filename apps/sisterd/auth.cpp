#include "auth.hpp"

#include <openssl/crypto.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/sha.h>

#include <algorithm>
#include <array>
#include <charconv>
#include <cctype>
#include <fstream>
#include <iomanip>
#include <regex>
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

std::string randomUuid() {
    std::array<unsigned char, 16> bytes{};
    if (RAND_bytes(bytes.data(), static_cast<int>(bytes.size())) != 1) {
        throw std::runtime_error("secure random generation failed");
    }
    bytes[6] = static_cast<unsigned char>((bytes[6] & 0x0fU) | 0x40U);
    bytes[8] = static_cast<unsigned char>((bytes[8] & 0x3fU) | 0x80U);
    const auto hex = hexEncode(bytes.data(), bytes.size());
    return hex.substr(0, 8) + '-' + hex.substr(8, 4) + '-' +
        hex.substr(12, 4) + '-' + hex.substr(16, 4) + '-' + hex.substr(20);
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

std::string trim(std::string value) {
    const auto first = value.find_first_not_of(" \t\n\r");
    if (first == std::string::npos) return "";
    const auto last = value.find_last_not_of(" \t\n\r");
    return value.substr(first, last - first + 1);
}

std::string normalizeEmail(std::string email) {
    email = trim(email);
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

bool validUuid(const std::string& value) {
    static const std::regex pattern(
        "^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
        "[89ab][0-9a-f]{3}-[0-9a-f]{12}$");
    return std::regex_match(value, pattern);
}

} // namespace

AuthStore::AuthStore(std::filesystem::path path)
    : path_(std::move(path)), sessionsPath_(path_.string() + ".sessions") {
    load();
    loadSessions();
}

void AuthStore::load() {
    std::lock_guard lock(mutex_);
    users_.clear();

    std::ifstream input(path_);
    std::string line;
    while (std::getline(input, line)) {
        if (line.empty()) continue;
        std::istringstream row(line);
        std::vector<std::string> fields;
        std::string field;
        while (std::getline(row, field, '\t')) {
            fields.push_back(field);
        }
        if (fields.size() == 6) {
            StoredUser user;
            user.publicUser.id = fields[0];
            user.publicUser.name = fields[1];
            user.publicUser.email = fields[2];
            user.publicUser.role = fields[3];
            user.salt = fields[4];
            user.passwordHash = fields[5];
            if (!user.publicUser.id.empty()) {
                users_.push_back(std::move(user));
            }
        } else if (fields.size() == 5) {
            StoredUser user;
            user.publicUser.id = fields[0];
            user.publicUser.name = fields[1];
            user.publicUser.email = fields[2];
            user.publicUser.role = "user";
            user.salt = fields[3];
            user.passwordHash = fields[4];
            if (!user.publicUser.id.empty()) {
                users_.push_back(std::move(user));
            }
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

void AuthStore::loadSessions() {
    std::lock_guard lock(mutex_);
    sessionsByTokenHash_.clear();

    std::ifstream input(sessionsPath_);
    std::string line;
    const auto now = std::chrono::system_clock::now();
    while (std::getline(input, line)) {
        std::istringstream row(line);
        std::string tokenHash;
        std::string userId;
        std::string expiresValue;
        if (!std::getline(row, tokenHash, '\t') || !std::getline(row, userId, '\t') ||
            !std::getline(row, expiresValue) || tokenHash.size() != SHA256_DIGEST_LENGTH * 2 ||
            !std::all_of(tokenHash.begin(), tokenHash.end(), [](unsigned char value) {
                return std::isdigit(value) || (value >= 'a' && value <= 'f');
            })) {
            continue;
        }

        std::int64_t expiresSeconds = 0;
        const auto [pointer, error] = std::from_chars(
            expiresValue.data(), expiresValue.data() + expiresValue.size(), expiresSeconds);
        if (error != std::errc{} || pointer != expiresValue.data() + expiresValue.size()) continue;

        const auto expiresAt = std::chrono::system_clock::time_point{
            std::chrono::seconds{expiresSeconds}};
        const bool knownUser = std::any_of(users_.begin(), users_.end(), [&](const StoredUser& user) {
            return user.publicUser.id == userId;
        });
        if (knownUser && expiresAt > now) sessionsByTokenHash_[tokenHash] = {userId, expiresAt};
    }
}

void AuthStore::saveSessions() const {
    std::filesystem::create_directories(sessionsPath_.parent_path());
    const auto temporary = sessionsPath_.string() + ".tmp";
    {
        std::ofstream output(temporary, std::ios::trunc);
        if (!output) throw std::runtime_error("unable to persist sessions");
        for (const auto& [tokenHash, session] : sessionsByTokenHash_) {
            const auto expiresSeconds = std::chrono::duration_cast<std::chrono::seconds>(
                session.expiresAt.time_since_epoch()).count();
            output << tokenHash << '\t' << session.userId << '\t' << expiresSeconds << '\n';
        }
    }
    std::filesystem::permissions(
        temporary,
        std::filesystem::perms::owner_read | std::filesystem::perms::owner_write,
        std::filesystem::perm_options::replace);
    std::filesystem::rename(temporary, sessionsPath_);
}

bool AuthStore::bootstrapOpen() const {
    std::lock_guard lock(mutex_);
    return users_.empty();
}

AuthResult AuthStore::createSession(const StoredUser& user) {
    const auto token = randomHex(32);
    const auto session_token_hash = sha256(token);
    sessionsByTokenHash_[session_token_hash] = {
        user.publicUser.id,
        std::chrono::system_clock::now() + sessionLifetime};
    saveSessions();
    return {user.publicUser, token};
}

std::optional<AuthResult> AuthStore::registerAdmin(
    const std::string& name,
    const std::string& rawEmail,
    const std::string& password) {
    std::lock_guard lock(mutex_);
    const auto created = bootstrapAdminUnlocked(name, rawEmail, password);
    if (!created) return std::nullopt;
    return createSession(users_.back());
}

std::optional<AuthUser> AuthStore::bootstrapAdmin(
    const std::string& name,
    const std::string& rawEmail,
    const std::string& password) {
    std::lock_guard lock(mutex_);
    return bootstrapAdminUnlocked(name, rawEmail, password);
}

std::optional<AuthUser> AuthStore::bootstrapAdminUnlocked(
    const std::string& name,
    const std::string& rawEmail,
    const std::string& password) {
    const auto email = normalizeEmail(rawEmail);
    if (!users_.empty() || name.size() < 2 || password.size() < 12 ||
        email.find('@') == std::string::npos || !validField(name) || !validField(email)) {
        return std::nullopt;
    }

    StoredUser user;
    user.publicUser = {randomUuid(), name, email, "admin"};
    user.salt = randomHex(16);
    user.passwordHash = passwordHash(password, user.salt);
    users_.push_back(user);
    save();
    return users_.back().publicUser;
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
    const std::string& rawName,
    const std::string& rawEmail,
    const std::string& password,
    const std::string& role,
    std::string* errorOut) {
    std::lock_guard lock(mutex_);
    const auto name = trim(rawName);
    const auto email = normalizeEmail(rawEmail);
    const bool duplicate = std::any_of(users_.begin(), users_.end(), [&](const StoredUser& user) {
        return user.publicUser.email == email;
    });
    const bool validRole = (role == "admin" || role == "user" || role == "registered_user" ||
                            role == "researcher" || role == "project_lead" || role == "guest");

    if (duplicate) {
        if (errorOut) *errorOut = "E-mail já cadastrado.";
        return std::nullopt;
    }
    if (name.size() < 2 || !validField(name)) {
        if (errorOut) *errorOut = "O nome deve ter no mínimo 2 caracteres válidos.";
        return std::nullopt;
    }
    if (email.find('@') == std::string::npos || !validField(email)) {
        if (errorOut) *errorOut = "Formato de e-mail inválido.";
        return std::nullopt;
    }
    if (password.size() < 12) {
        if (errorOut) *errorOut = "A senha temporária deve ter no mínimo 12 caracteres.";
        return std::nullopt;
    }
    if (!validRole) {
        if (errorOut) *errorOut = "Papel de usuário inválido.";
        return std::nullopt;
    }

    StoredUser user;
    user.publicUser = {randomUuid(), name, email, role};
    user.salt = randomHex(16);
    user.passwordHash = passwordHash(password, user.salt);
    users_.push_back(user);
    save();
    return users_.back().publicUser;
}

std::optional<AuthUser> AuthStore::updateUser(
    const std::string& id,
    const std::string& rawName,
    const std::string& rawEmail,
    const std::string& role,
    const std::string& optionalPassword,
    std::string* errorOut) {
    std::lock_guard lock(mutex_);
    const auto name = trim(rawName);
    const auto email = normalizeEmail(rawEmail);
    const auto target = std::find_if(users_.begin(), users_.end(), [&](const StoredUser& user) {
        return user.publicUser.id == id;
    });

    if (target == users_.end()) {
        if (errorOut) *errorOut = "Usuário não encontrado.";
        return std::nullopt;
    }

    const bool duplicate = std::any_of(users_.begin(), users_.end(), [&](const StoredUser& user) {
        return user.publicUser.id != id && user.publicUser.email == email;
    });
    if (duplicate) {
        if (errorOut) *errorOut = "E-mail já cadastrado para outra pessoa.";
        return std::nullopt;
    }

    if (name.size() < 2 || !validField(name)) {
        if (errorOut) *errorOut = "O nome deve ter no mínimo 2 caracteres válidos.";
        return std::nullopt;
    }
    if (email.find('@') == std::string::npos || !validField(email)) {
        if (errorOut) *errorOut = "Formato de e-mail inválido.";
        return std::nullopt;
    }

    const bool validRole = (role == "admin" || role == "user" || role == "registered_user" ||
                            role == "researcher" || role == "project_lead" || role == "guest");
    if (!validRole) {
        if (errorOut) *errorOut = "Papel de usuário inválido.";
        return std::nullopt;
    }

    if (target->publicUser.role == "admin" && role != "admin") {
        const auto adminCount = std::count_if(users_.begin(), users_.end(), [](const StoredUser& user) {
            return user.publicUser.role == "admin";
        });
        if (adminCount <= 1) {
            if (errorOut) *errorOut = "Não é possível alterar o papel do único administrador do sistema.";
            return std::nullopt;
        }
    }

    if (!optionalPassword.empty()) {
        if (optionalPassword.size() < 12) {
            if (errorOut) *errorOut = "A nova senha temporária deve ter no mínimo 12 caracteres.";
            return std::nullopt;
        }
        target->salt = randomHex(16);
        target->passwordHash = passwordHash(optionalPassword, target->salt);
    }

    target->publicUser.name = name;
    target->publicUser.email = email;
    target->publicUser.role = role;
    save();
    return target->publicUser;
}

bool AuthStore::deleteUser(
    const std::string& id,
    const std::string& currentActorId,
    std::string* errorOut) {
    std::lock_guard lock(mutex_);
    const auto target = std::find_if(users_.begin(), users_.end(), [&](const StoredUser& user) {
        return user.publicUser.id == id;
    });

    if (target == users_.end()) {
        if (errorOut) *errorOut = "Usuário não encontrado.";
        return false;
    }

    if (id == currentActorId) {
        if (errorOut) *errorOut = "Você não pode excluir a sua própria conta logada.";
        return false;
    }

    if (target->publicUser.role == "admin") {
        const auto adminCount = std::count_if(users_.begin(), users_.end(), [](const StoredUser& user) {
            return user.publicUser.role == "admin";
        });
        if (adminCount <= 1) {
            if (errorOut) *errorOut = "Não é possível excluir o único administrador do sistema.";
            return false;
        }
    }

    users_.erase(target);
    for (auto it = sessionsByTokenHash_.begin(); it != sessionsByTokenHash_.end();) {
        if (it->second.userId == id) {
            it = sessionsByTokenHash_.erase(it);
        } else {
            ++it;
        }
    }

    save();
    saveSessions();
    return true;
}

std::optional<AuthUser> AuthStore::importUser(
    const std::string& id,
    const std::string& name,
    const std::string& rawEmail,
    const std::string& password,
    const std::string& role) {
    std::lock_guard lock(mutex_);
    const auto email = normalizeEmail(rawEmail);
    const bool duplicate = std::any_of(users_.begin(), users_.end(), [&](const StoredUser& user) {
        return user.publicUser.id == id || user.publicUser.email == email;
    });
    const bool validRole = (role == "admin" || role == "user" || role == "registered_user" ||
                            role == "researcher" || role == "project_lead" || role == "guest");
    if (duplicate || !validUuid(id) || name.size() < 2 || password.size() < 12 ||
        email.find('@') == std::string::npos || !validRole ||
        !validField(name) || !validField(email)) {
        return std::nullopt;
    }

    StoredUser user;
    user.publicUser = {id, name, email, role};
    user.salt = randomHex(16);
    user.passwordHash = passwordHash(password, user.salt);
    users_.push_back(user);
    save();
    return users_.back().publicUser;
}

std::optional<AuthUser> AuthStore::userForToken(const std::string& token) {
    if (token.empty()) return std::nullopt;
    std::lock_guard lock(mutex_);
    const auto session_token_hash = sha256(token);
    const auto session = sessionsByTokenHash_.find(session_token_hash);
    if (session == sessionsByTokenHash_.end()) return std::nullopt;
    if (session->second.expiresAt <= std::chrono::system_clock::now()) {
        sessionsByTokenHash_.erase(session);
        saveSessions();
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
    const auto session_token_hash = sha256(token);
    sessionsByTokenHash_.erase(session_token_hash);
    saveSessions();
}

} // namespace sisterd
