#pragma once

#include <chrono>
#include <filesystem>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

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
    explicit AuthStore(std::filesystem::path path);

    bool bootstrapOpen() const;
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
    mutable std::mutex mutex_;
    std::vector<StoredUser> users_;
    std::unordered_map<std::string, Session> sessions_;

    void load();
    void save() const;
    AuthResult createSession(const StoredUser& user);
};

} // namespace sisterd
