#include "auth.hpp"

#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>

namespace {

void expect(bool condition, const std::string& message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

} // namespace

int main() {
    const auto suffix = std::to_string(
        std::chrono::steady_clock::now().time_since_epoch().count());
    const auto authFile =
        std::filesystem::temp_directory_path() / ("sister-auth-test-" + suffix + ".tsv");

    {
        sisterd::AuthStore auth(authFile);
        expect(auth.bootstrapOpen(), "new store should accept bootstrap");

        const auto registered = auth.registerAdmin(
            "Equipe SisTer", "ADMIN@SISTER.LOCAL", "senha-segura-123");
        expect(registered.has_value(), "first administrator should be created");
        expect(registered->user.role == "admin", "bootstrap user should be administrator");
        expect(
            registered->user.email == "admin@sister.local",
            "email should be normalized");
        expect(!auth.bootstrapOpen(), "bootstrap should close after first user");
        expect(
            !auth.registerAdmin("Outro", "outro@sister.local", "outra-senha-123"),
            "second bootstrap registration should fail");
        const auto member = auth.createUser(
            "Pessoa Usuária", "pessoa@sister.local", "senha-de-equipe-123", "user");
        expect(member.has_value(), "administrator workflow should create team member");
        expect(member->role == "user", "managed role should be retained");
        expect(auth.users().size() == 2, "user listing should include both accounts");
        expect(
            !auth.createUser(
                "Duplicada", "pessoa@sister.local", "senha-de-equipe-456", "admin"),
            "duplicate email should fail");
        expect(
            !auth.login("admin@sister.local", "senha-incorreta"),
            "wrong password should fail");

        const auto login = auth.login("admin@sister.local", "senha-segura-123");
        expect(login.has_value(), "valid password should authenticate");
        expect(
            auth.userForToken(login->token).has_value(),
            "issued token should identify its user");
        auth.logout(login->token);
        expect(
            !auth.userForToken(login->token),
            "revoked token should not identify a user");
    }

    {
        sisterd::AuthStore auth(authFile);
        expect(!auth.bootstrapOpen(), "user should persist across restart");
        expect(
            auth.login("admin@sister.local", "senha-segura-123").has_value(),
            "persisted user should authenticate");
    }

    std::filesystem::remove(authFile);
    std::cout << "sisterd_auth_tests ok\n";
    return 0;
}
