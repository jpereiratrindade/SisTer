#pragma once

#include <chrono>
#include <filesystem>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

struct pg_conn;

namespace sisterd {

struct AuthUser {
    std::string id;
    std::string name;
    std::string email;
    std::string role;
};

struct AuthResult {
    AuthUser user;
    std::string token;
};

class AuthStore {
public:
    explicit AuthStore(
        std::filesystem::path path,
        std::string databaseUrl = {});
    ~AuthStore();

    AuthStore(const AuthStore&) = delete;
    AuthStore& operator=(const AuthStore&) = delete;

    [[nodiscard]] static std::string normalizeIdentity(std::string identity);
    [[nodiscard]] bool databaseBacked() const noexcept;
    [[nodiscard]] std::string_view backendName() const noexcept;

    bool bootstrapOpen() const;
    std::optional<AuthUser> bootstrapAdmin(
        const std::string& name,
        const std::string& email,
        const std::string& password);
    std::optional<AuthResult> registerAdmin(
        const std::string& name,
        const std::string& email,
        const std::string& password);
    std::optional<AuthResult> login(const std::string& email, const std::string& password);
    std::optional<AuthUser> userForToken(const std::string& token);
    std::vector<AuthUser> users() const;
    std::optional<AuthUser> createUser(
        const std::string& name,
        const std::string& email,
        const std::string& password,
        const std::string& role,
        std::string* errorOut = nullptr);
    std::optional<AuthUser> updateUser(
        const std::string& id,
        const std::string& name,
        const std::string& email,
        const std::string& role,
        const std::string& optionalPassword,
        std::string* errorOut = nullptr);
    bool deleteUser(
        const std::string& id,
        const std::string& currentActorId,
        std::string* errorOut = nullptr);
    std::optional<AuthUser> importUser(
        const std::string& id,
        const std::string& name,
        const std::string& email,
        const std::string& password,
        const std::string& role);
    void logout(const std::string& token);

private:
    struct StoredUser {
        AuthUser publicUser;
        std::string salt;
        std::string passwordHash;
    };

    struct Session {
        std::string userId;
        std::chrono::system_clock::time_point expiresAt;
    };

    std::filesystem::path path_;
    std::filesystem::path sessionsPath_;
    std::string databaseUrl_;
    mutable pg_conn* databaseConn_ = nullptr;
    mutable std::mutex mutex_;
    std::vector<StoredUser> users_;
    std::unordered_map<std::string, Session> sessionsByTokenHash_;

    void load();
    void save() const;
    void loadSessions();
    void saveSessions() const;
    std::optional<AuthUser> bootstrapAdminUnlocked(
        const std::string& name,
        const std::string& email,
        const std::string& password);
    AuthResult createSession(const StoredUser& user);

    void connectDatabase();
    void disconnectDatabase();
    [[nodiscard]] bool ensureDatabaseConnected() const;
    [[nodiscard]] bool databaseBootstrapOpen() const;
    std::optional<AuthUser> databaseBootstrapAdmin(
        const std::string& name,
        const std::string& email,
        const std::string& password);
    std::optional<AuthResult> databaseRegisterAdmin(
        const std::string& name,
        const std::string& email,
        const std::string& password);
    std::optional<AuthResult> databaseLogin(
        const std::string& email,
        const std::string& password);
    std::optional<AuthUser> databaseUserForToken(const std::string& token);
    std::vector<AuthUser> databaseUsers() const;
    std::optional<AuthUser> databaseCreateUser(
        const std::string& name,
        const std::string& email,
        const std::string& password,
        const std::string& role,
        std::string* errorOut);
    std::optional<AuthUser> databaseUpdateUser(
        const std::string& id,
        const std::string& name,
        const std::string& email,
        const std::string& role,
        const std::string& optionalPassword,
        std::string* errorOut);
    bool databaseDeleteUser(
        const std::string& id,
        const std::string& currentActorId,
        std::string* errorOut);
    std::optional<AuthUser> databaseImportUser(
        const std::string& id,
        const std::string& name,
        const std::string& email,
        const std::string& password,
        const std::string& role);
    void databaseLogout(const std::string& token);
};

} // namespace sisterd
