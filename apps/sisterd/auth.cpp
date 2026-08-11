#include "auth.hpp"

#include <openssl/crypto.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/sha.h>

#ifdef SISTER_HAVE_LIBPQ
#include <libpq-fe.h>
#endif

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

std::string passwordHash(
    const std::string& password,
    const std::string& saltHex,
    int iterations = passwordIterations) {
    const auto salt = hexDecode(saltHex);
    std::array<unsigned char, 32> output{};
    if (salt.empty() ||
        PKCS5_PBKDF2_HMAC(
            password.data(),
            static_cast<int>(password.size()),
            salt.data(),
            static_cast<int>(salt.size()),
            iterations,
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

AuthStore::AuthStore(
    std::filesystem::path path,
    std::string databaseUrl)
    : path_(std::move(path)),
      sessionsPath_(path_.string() + ".sessions"),
      databaseUrl_(std::move(databaseUrl)) {
    if (databaseBacked()) {
        connectDatabase();
        if (!ensureDatabaseConnected()) {
            throw std::runtime_error("database-backed authentication is unavailable");
        }
        return;
    }
    load();
    loadSessions();
}

AuthStore::~AuthStore() {
    disconnectDatabase();
}

std::string AuthStore::normalizeIdentity(std::string identity) {
    return normalizeEmail(std::move(identity));
}

bool AuthStore::databaseBacked() const noexcept {
    return !databaseUrl_.empty();
}

std::string_view AuthStore::backendName() const noexcept {
    return databaseBacked() ? "postgresql" : "file";
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
    if (databaseBacked()) return databaseBootstrapOpen();
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
    if (databaseBacked()) return databaseRegisterAdmin(name, rawEmail, password);
    const auto created = bootstrapAdminUnlocked(name, rawEmail, password);
    if (!created) return std::nullopt;
    return createSession(users_.back());
}

std::optional<AuthUser> AuthStore::bootstrapAdmin(
    const std::string& name,
    const std::string& rawEmail,
    const std::string& password) {
    std::lock_guard lock(mutex_);
    if (databaseBacked()) return databaseBootstrapAdmin(name, rawEmail, password);
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
    if (databaseBacked()) return databaseLogin(rawEmail, password);
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
    if (databaseBacked()) return databaseUsers();
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
    if (databaseBacked()) return databaseCreateUser(rawName, rawEmail, password, role, errorOut);
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
    if (databaseBacked()) return databaseUpdateUser(id, rawName, rawEmail, role, optionalPassword, errorOut);
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
    if (databaseBacked()) return databaseDeleteUser(id, currentActorId, errorOut);
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
    if (databaseBacked()) return databaseImportUser(id, name, rawEmail, password, role);
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
    if (databaseBacked()) return databaseUserForToken(token);
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
    if (databaseBacked()) {
        databaseLogout(token);
        return;
    }
    const auto session_token_hash = sha256(token);
    sessionsByTokenHash_.erase(session_token_hash);
    saveSessions();
}


void AuthStore::connectDatabase() {
    if (!databaseBacked() || databaseConn_ != nullptr) return;
#ifdef SISTER_HAVE_LIBPQ
    databaseConn_ = PQconnectdb(databaseUrl_.c_str());
    if (databaseConn_ == nullptr || PQstatus(databaseConn_) != CONNECTION_OK) {
        if (databaseConn_ != nullptr) {
            PQfinish(databaseConn_);
            databaseConn_ = nullptr;
        }
    }
#else
    throw std::runtime_error(
        "PostgreSQL authentication requested but sisterd was built without libpq");
#endif
}

void AuthStore::disconnectDatabase() {
#ifdef SISTER_HAVE_LIBPQ
    if (databaseConn_ != nullptr) {
        PQfinish(databaseConn_);
        databaseConn_ = nullptr;
    }
#else
    databaseConn_ = nullptr;
#endif
}

bool AuthStore::ensureDatabaseConnected() const {
    if (!databaseBacked()) return false;
#ifdef SISTER_HAVE_LIBPQ
    if (databaseConn_ == nullptr) {
        const_cast<AuthStore*>(this)->connectDatabase();
    }
    if (databaseConn_ == nullptr) return false;
    if (PQstatus(databaseConn_) == CONNECTION_OK) return true;
    PQreset(databaseConn_);
    return PQstatus(databaseConn_) == CONNECTION_OK;
#else
    return false;
#endif
}

bool AuthStore::databaseBootstrapOpen() const {
#ifdef SISTER_HAVE_LIBPQ
    if (!ensureDatabaseConnected()) return false;
    PGresult* result = PQexec(
        databaseConn_,
        "SELECT NOT EXISTS (SELECT 1 FROM sister_users)");
    const bool open = PQresultStatus(result) == PGRES_TUPLES_OK &&
        PQntuples(result) == 1 && std::string(PQgetvalue(result, 0, 0)) == "t";
    PQclear(result);
    return open;
#else
    return false;
#endif
}

std::optional<AuthUser> AuthStore::databaseBootstrapAdmin(
    const std::string& rawName,
    const std::string& rawEmail,
    const std::string& password) {
#ifdef SISTER_HAVE_LIBPQ
    const auto name = trim(rawName);
    const auto email = normalizeEmail(rawEmail);
    if (name.size() < 2 || password.size() < 12 || email.find('@') == std::string::npos ||
        !validField(name) || !validField(email) || !ensureDatabaseConnected()) {
        return std::nullopt;
    }

    const std::string id = randomUuid();
    const std::string salt = randomHex(16);
    const std::string hash = passwordHash(password, salt);
    const std::string iterations = std::to_string(passwordIterations);
    const char* values[] = {
        id.c_str(), email.c_str(), name.c_str(), salt.c_str(), hash.c_str(), iterations.c_str()};
    PGresult* result = PQexecParams(
        databaseConn_,
        "INSERT INTO sister_users "
        "(user_id,email,full_name,global_role,password_salt,password_hash,password_iterations,active,updated_at) "
        "SELECT $1,$2,$3,'admin',$4,$5,$6::integer,true,now() "
        "WHERE NOT EXISTS (SELECT 1 FROM sister_users) "
        "RETURNING user_id, full_name, email, global_role",
        6, nullptr, values, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        PQclear(result);
        return std::nullopt;
    }
    AuthUser user{PQgetvalue(result, 0, 0), PQgetvalue(result, 0, 1),
                  PQgetvalue(result, 0, 2), PQgetvalue(result, 0, 3)};
    PQclear(result);
    return user;
#else
    (void)rawName; (void)rawEmail; (void)password;
    return std::nullopt;
#endif
}

std::optional<AuthResult> AuthStore::databaseRegisterAdmin(
    const std::string& name,
    const std::string& email,
    const std::string& password) {
#ifdef SISTER_HAVE_LIBPQ
    if (!ensureDatabaseConnected()) return std::nullopt;
    PGresult* transaction = PQexec(databaseConn_, "BEGIN");
    const bool began = PQresultStatus(transaction) == PGRES_COMMAND_OK;
    PQclear(transaction);
    if (!began) return std::nullopt;

    const auto created = databaseBootstrapAdmin(name, email, password);
    if (!created) {
        transaction = PQexec(databaseConn_, "ROLLBACK");
        PQclear(transaction);
        return std::nullopt;
    }

    const std::string token = randomHex(32);
    const std::string tokenHash = sha256(token);
    const std::string sessionId = randomUuid();
    const char* values[] = {sessionId.c_str(), created->id.c_str(), tokenHash.c_str()};
    PGresult* result = PQexecParams(
        databaseConn_,
        "INSERT INTO sister_sessions "
        "(session_id,user_id,session_token_hash,issued_at,expires_at) "
        "VALUES ($1,$2,$3,now(),now() + interval '8 hours')",
        3, nullptr, values, nullptr, nullptr, 0);
    const bool inserted = PQresultStatus(result) == PGRES_COMMAND_OK;
    PQclear(result);
    if (!inserted) {
        transaction = PQexec(databaseConn_, "ROLLBACK");
        PQclear(transaction);
        return std::nullopt;
    }

    transaction = PQexec(databaseConn_, "COMMIT");
    const bool committed = PQresultStatus(transaction) == PGRES_COMMAND_OK;
    PQclear(transaction);
    if (!committed) return std::nullopt;
    return AuthResult{*created, token};
#else
    (void)name; (void)email; (void)password;
    return std::nullopt;
#endif
}

std::optional<AuthResult> AuthStore::databaseLogin(
    const std::string& rawEmail,
    const std::string& password) {
#ifdef SISTER_HAVE_LIBPQ
    if (!ensureDatabaseConnected()) return std::nullopt;
    const std::string email = normalizeEmail(rawEmail);
    const char* values[] = {email.c_str()};
    PGresult* result = PQexecParams(
        databaseConn_,
        "SELECT user_id, full_name, email, global_role, password_salt, password_hash, password_iterations "
        "FROM sister_users "
        "WHERE lower(email)=lower($1) AND active AND password_hash IS NOT NULL LIMIT 1",
        1, nullptr, values, nullptr, nullptr, 0);

    const bool found = PQresultStatus(result) == PGRES_TUPLES_OK && PQntuples(result) == 1;
    const std::string fallbackSalt(32, '0');
    std::string salt = fallbackSalt;
    std::string expected(64, '0');
    int iterations = passwordIterations;
    AuthUser user;
    if (found) {
        user = {PQgetvalue(result, 0, 0), PQgetvalue(result, 0, 1),
                PQgetvalue(result, 0, 2), PQgetvalue(result, 0, 3)};
        salt = PQgetvalue(result, 0, 4);
        expected = PQgetvalue(result, 0, 5);
        const std::string iterationText = PQgetvalue(result, 0, 6);
        const auto [ptr, error] = std::from_chars(
            iterationText.data(), iterationText.data() + iterationText.size(), iterations);
        if (error != std::errc{} || ptr != iterationText.data() + iterationText.size() ||
            iterations < 10000 || iterations > 2000000) {
            iterations = passwordIterations;
        }
    }
    PQclear(result);

    const std::string candidate = passwordHash(password, salt, iterations);
    const bool valid = found && candidate.size() == expected.size() &&
        CRYPTO_memcmp(candidate.data(), expected.data(), candidate.size()) == 0;
    if (!valid) return std::nullopt;

    const std::string token = randomHex(32);
    const std::string tokenHash = sha256(token);
    const std::string sessionId = randomUuid();
    const char* sessionValues[] = {sessionId.c_str(), user.id.c_str(), tokenHash.c_str()};
    result = PQexecParams(
        databaseConn_,
        "INSERT INTO sister_sessions "
        "(session_id,user_id,session_token_hash,issued_at,expires_at) "
        "VALUES ($1,$2,$3,now(),now() + interval '8 hours')",
        3, nullptr, sessionValues, nullptr, nullptr, 0);
    const bool sessionCreated = PQresultStatus(result) == PGRES_COMMAND_OK;
    PQclear(result);
    if (!sessionCreated) return std::nullopt;
    return AuthResult{user, token};
#else
    (void)rawEmail; (void)password;
    return std::nullopt;
#endif
}

std::optional<AuthUser> AuthStore::databaseUserForToken(const std::string& token) {
#ifdef SISTER_HAVE_LIBPQ
    if (!ensureDatabaseConnected()) return std::nullopt;
    const std::string tokenHash = sha256(token);
    const char* values[] = {tokenHash.c_str()};
    PGresult* result = PQexecParams(
        databaseConn_,
        "SELECT u.user_id, u.full_name, u.email, u.global_role "
        "FROM sister_sessions s JOIN sister_users u ON u.user_id=s.user_id "
        "WHERE s.session_token_hash=$1 AND s.revoked_at IS NULL "
        "AND s.expires_at > now() AND u.active LIMIT 1",
        1, nullptr, values, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        PQclear(result);
        return std::nullopt;
    }
    AuthUser user{PQgetvalue(result, 0, 0), PQgetvalue(result, 0, 1),
                  PQgetvalue(result, 0, 2), PQgetvalue(result, 0, 3)};
    PQclear(result);
    return user;
#else
    (void)token;
    return std::nullopt;
#endif
}

std::vector<AuthUser> AuthStore::databaseUsers() const {
    std::vector<AuthUser> users;
#ifdef SISTER_HAVE_LIBPQ
    if (!ensureDatabaseConnected()) return users;
    PGresult* result = PQexec(
        databaseConn_,
        "SELECT user_id, full_name, email, global_role "
        "FROM sister_users WHERE active ORDER BY lower(email), user_id");
    if (PQresultStatus(result) != PGRES_TUPLES_OK) {
        PQclear(result);
        return users;
    }
    users.reserve(static_cast<std::size_t>(PQntuples(result)));
    for (int row = 0; row < PQntuples(result); ++row) {
        users.push_back({PQgetvalue(result, row, 0), PQgetvalue(result, row, 1),
                         PQgetvalue(result, row, 2), PQgetvalue(result, row, 3)});
    }
    PQclear(result);
#endif
    return users;
}

std::optional<AuthUser> AuthStore::databaseCreateUser(
    const std::string& rawName,
    const std::string& rawEmail,
    const std::string& password,
    const std::string& role,
    std::string* errorOut) {
#ifdef SISTER_HAVE_LIBPQ
    const std::string name = trim(rawName);
    const std::string email = normalizeEmail(rawEmail);
    const bool validRole = role == "admin" || role == "user" || role == "registered_user" ||
        role == "researcher" || role == "project_lead" || role == "guest";
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
    if (!ensureDatabaseConnected()) {
        if (errorOut) *errorOut = "Banco de identidades indisponível.";
        return std::nullopt;
    }

    const std::string id = randomUuid();
    const std::string salt = randomHex(16);
    const std::string hash = passwordHash(password, salt);
    const std::string iterations = std::to_string(passwordIterations);
    const char* values[] = {id.c_str(), email.c_str(), name.c_str(), role.c_str(),
                            salt.c_str(), hash.c_str(), iterations.c_str()};
    PGresult* result = PQexecParams(
        databaseConn_,
        "INSERT INTO sister_users "
        "(user_id,email,full_name,global_role,password_salt,password_hash,password_iterations,active,updated_at) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7::integer,true,now()) "
        "RETURNING user_id, full_name, email, global_role",
        7, nullptr, values, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        const char* sqlState = PQresultErrorField(result, PG_DIAG_SQLSTATE);
        if (errorOut) {
            *errorOut = sqlState != nullptr && std::string(sqlState) == "23505"
                ? "E-mail já cadastrado." : "Não foi possível persistir o usuário.";
        }
        PQclear(result);
        return std::nullopt;
    }
    AuthUser user{PQgetvalue(result, 0, 0), PQgetvalue(result, 0, 1),
                  PQgetvalue(result, 0, 2), PQgetvalue(result, 0, 3)};
    PQclear(result);
    return user;
#else
    (void)rawName; (void)rawEmail; (void)password; (void)role;
    if (errorOut) *errorOut = "Banco de identidades indisponível.";
    return std::nullopt;
#endif
}

std::optional<AuthUser> AuthStore::databaseUpdateUser(
    const std::string& id,
    const std::string& rawName,
    const std::string& rawEmail,
    const std::string& role,
    const std::string& optionalPassword,
    std::string* errorOut) {
#ifdef SISTER_HAVE_LIBPQ
    const std::string name = trim(rawName);
    const std::string email = normalizeEmail(rawEmail);
    const bool validRole = role == "admin" || role == "user" || role == "registered_user" ||
        role == "researcher" || role == "project_lead" || role == "guest";
    if (name.size() < 2 || !validField(name)) {
        if (errorOut) *errorOut = "O nome deve ter no mínimo 2 caracteres válidos.";
        return std::nullopt;
    }
    if (email.find('@') == std::string::npos || !validField(email)) {
        if (errorOut) *errorOut = "Formato de e-mail inválido.";
        return std::nullopt;
    }
    if (!validRole) {
        if (errorOut) *errorOut = "Papel de usuário inválido.";
        return std::nullopt;
    }
    if (!optionalPassword.empty() && optionalPassword.size() < 12) {
        if (errorOut) *errorOut = "A nova senha temporária deve ter no mínimo 12 caracteres.";
        return std::nullopt;
    }
    if (!ensureDatabaseConnected()) {
        if (errorOut) *errorOut = "Banco de identidades indisponível.";
        return std::nullopt;
    }

    const char* idValue[] = {id.c_str()};
    PGresult* result = PQexecParams(
        databaseConn_,
        "SELECT global_role FROM sister_users WHERE user_id=$1 AND active",
        1, nullptr, idValue, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        if (errorOut) *errorOut = "Usuário não encontrado.";
        PQclear(result);
        return std::nullopt;
    }
    const std::string currentRole = PQgetvalue(result, 0, 0);
    PQclear(result);

    const char* duplicateValues[] = {email.c_str(), id.c_str()};
    result = PQexecParams(
        databaseConn_,
        "SELECT 1 FROM sister_users WHERE lower(email)=lower($1) AND user_id<>$2 LIMIT 1",
        2, nullptr, duplicateValues, nullptr, nullptr, 0);
    const bool duplicate = PQresultStatus(result) == PGRES_TUPLES_OK && PQntuples(result) > 0;
    PQclear(result);
    if (duplicate) {
        if (errorOut) *errorOut = "E-mail já cadastrado para outra pessoa.";
        return std::nullopt;
    }

    if (currentRole == "admin" && role != "admin") {
        result = PQexec(databaseConn_,
            "SELECT count(*) FROM sister_users WHERE active AND global_role='admin'");
        const bool soleAdmin = PQresultStatus(result) == PGRES_TUPLES_OK &&
            PQntuples(result) == 1 && std::string(PQgetvalue(result, 0, 0)) == "1";
        PQclear(result);
        if (soleAdmin) {
            if (errorOut) *errorOut = "Não é possível alterar o papel do único administrador do sistema.";
            return std::nullopt;
        }
    }

    if (optionalPassword.empty()) {
        const char* values[] = {id.c_str(), name.c_str(), email.c_str(), role.c_str()};
        result = PQexecParams(
            databaseConn_,
            "UPDATE sister_users SET full_name=$2,email=$3,global_role=$4,updated_at=now() "
            "WHERE user_id=$1 AND active RETURNING user_id,full_name,email,global_role",
            4, nullptr, values, nullptr, nullptr, 0);
    } else {
        const std::string salt = randomHex(16);
        const std::string hash = passwordHash(optionalPassword, salt);
        const std::string iterations = std::to_string(passwordIterations);
        const char* values[] = {id.c_str(), name.c_str(), email.c_str(), role.c_str(),
                                salt.c_str(), hash.c_str(), iterations.c_str()};
        result = PQexecParams(
            databaseConn_,
            "WITH updated AS ("
            " UPDATE sister_users SET full_name=$2,email=$3,global_role=$4,password_salt=$5,"
            " password_hash=$6,password_iterations=$7::integer,updated_at=now() "
            " WHERE user_id=$1 AND active RETURNING user_id,full_name,email,global_role"
            "), revoked AS ("
            " UPDATE sister_sessions SET revoked_at=now() WHERE user_id=$1 AND revoked_at IS NULL"
            ") SELECT user_id,full_name,email,global_role FROM updated",
            7, nullptr, values, nullptr, nullptr, 0);
    }
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        const char* sqlState = PQresultErrorField(result, PG_DIAG_SQLSTATE);
        if (errorOut) {
            *errorOut = sqlState != nullptr && std::string(sqlState) == "23505"
                ? "E-mail já cadastrado para outra pessoa." : "Não foi possível persistir a atualização.";
        }
        PQclear(result);
        return std::nullopt;
    }
    AuthUser user{PQgetvalue(result, 0, 0), PQgetvalue(result, 0, 1),
                  PQgetvalue(result, 0, 2), PQgetvalue(result, 0, 3)};
    PQclear(result);
    return user;
#else
    (void)id; (void)rawName; (void)rawEmail; (void)role; (void)optionalPassword;
    if (errorOut) *errorOut = "Banco de identidades indisponível.";
    return std::nullopt;
#endif
}

bool AuthStore::databaseDeleteUser(
    const std::string& id,
    const std::string& currentActorId,
    std::string* errorOut) {
#ifdef SISTER_HAVE_LIBPQ
    if (id == currentActorId) {
        if (errorOut) *errorOut = "Você não pode excluir a sua própria conta logada.";
        return false;
    }
    if (!ensureDatabaseConnected()) {
        if (errorOut) *errorOut = "Banco de identidades indisponível.";
        return false;
    }
    const char* values[] = {id.c_str()};
    PGresult* result = PQexecParams(
        databaseConn_,
        "SELECT global_role FROM sister_users WHERE user_id=$1 AND active",
        1, nullptr, values, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        if (errorOut) *errorOut = "Usuário não encontrado.";
        PQclear(result);
        return false;
    }
    const std::string role = PQgetvalue(result, 0, 0);
    PQclear(result);
    if (role == "admin") {
        result = PQexec(databaseConn_,
            "SELECT count(*) FROM sister_users WHERE active AND global_role='admin'");
        const bool soleAdmin = PQresultStatus(result) == PGRES_TUPLES_OK &&
            PQntuples(result) == 1 && std::string(PQgetvalue(result, 0, 0)) == "1";
        PQclear(result);
        if (soleAdmin) {
            if (errorOut) *errorOut = "Não é possível excluir o único administrador do sistema.";
            return false;
        }
    }

    result = PQexecParams(
        databaseConn_,
        "WITH disabled AS ("
        " UPDATE sister_users SET active=false,updated_at=now() WHERE user_id=$1 AND active RETURNING user_id"
        "), revoked AS ("
        " UPDATE sister_sessions SET revoked_at=now() WHERE user_id=$1 AND revoked_at IS NULL"
        ") SELECT user_id FROM disabled",
        1, nullptr, values, nullptr, nullptr, 0);
    const bool disabled = PQresultStatus(result) == PGRES_TUPLES_OK && PQntuples(result) == 1;
    PQclear(result);
    if (!disabled && errorOut) *errorOut = "Não foi possível excluir o usuário.";
    return disabled;
#else
    (void)id; (void)currentActorId;
    if (errorOut) *errorOut = "Banco de identidades indisponível.";
    return false;
#endif
}

std::optional<AuthUser> AuthStore::databaseImportUser(
    const std::string& id,
    const std::string& rawName,
    const std::string& rawEmail,
    const std::string& password,
    const std::string& role) {
#ifdef SISTER_HAVE_LIBPQ
    const std::string name = trim(rawName);
    const std::string email = normalizeEmail(rawEmail);
    const bool validRole = role == "admin" || role == "user" || role == "registered_user" ||
        role == "researcher" || role == "project_lead" || role == "guest";
    if (!validUuid(id) || name.size() < 2 || password.size() < 12 ||
        email.find('@') == std::string::npos || !validRole ||
        !validField(name) || !validField(email) || !ensureDatabaseConnected()) {
        return std::nullopt;
    }
    const std::string salt = randomHex(16);
    const std::string hash = passwordHash(password, salt);
    const std::string iterations = std::to_string(passwordIterations);
    const char* values[] = {id.c_str(), email.c_str(), name.c_str(), role.c_str(),
                            salt.c_str(), hash.c_str(), iterations.c_str()};
    PGresult* result = PQexecParams(
        databaseConn_,
        "INSERT INTO sister_users "
        "(user_id,email,full_name,global_role,password_salt,password_hash,password_iterations,active,updated_at) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7::integer,true,now()) "
        "RETURNING user_id,full_name,email,global_role",
        7, nullptr, values, nullptr, nullptr, 0);
    if (PQresultStatus(result) != PGRES_TUPLES_OK || PQntuples(result) != 1) {
        PQclear(result);
        return std::nullopt;
    }
    AuthUser user{PQgetvalue(result, 0, 0), PQgetvalue(result, 0, 1),
                  PQgetvalue(result, 0, 2), PQgetvalue(result, 0, 3)};
    PQclear(result);
    return user;
#else
    (void)id; (void)rawName; (void)rawEmail; (void)password; (void)role;
    return std::nullopt;
#endif
}

void AuthStore::databaseLogout(const std::string& token) {
#ifdef SISTER_HAVE_LIBPQ
    if (!ensureDatabaseConnected()) return;
    const std::string tokenHash = sha256(token);
    const char* values[] = {tokenHash.c_str()};
    PGresult* result = PQexecParams(
        databaseConn_,
        "UPDATE sister_sessions SET revoked_at=now() "
        "WHERE session_token_hash=$1 AND revoked_at IS NULL",
        1, nullptr, values, nullptr, nullptr, 0);
    PQclear(result);
#else
    (void)token;
#endif
}

} // namespace sisterd
