#include "auth.hpp"

#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <regex>
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
    const auto offlineAuthFile =
        std::filesystem::temp_directory_path() / ("sister-offline-bootstrap-test-" + suffix + ".tsv");
    std::string persistentToken;

    {
        sisterd::AuthStore auth(offlineAuthFile);
        const auto administrator = auth.bootstrapAdmin(
            "Administrador Offline", "OFFLINE@SISTER.LOCAL", "senha-offline-123");
        expect(administrator.has_value(), "offline bootstrap should create administrator");
        expect(administrator->role == "admin", "offline bootstrap should assign admin role");
        expect(administrator->email == "offline@sister.local", "offline email should be normalized");
        expect(
            !std::filesystem::exists(offlineAuthFile.string() + ".sessions"),
            "offline bootstrap must not persist an unused session");
        expect(
            !auth.bootstrapAdmin("Outro", "outro@sister.local", "outra-senha-123"),
            "offline bootstrap should be single-use");
    }
    {
        sisterd::AuthStore auth(offlineAuthFile);
        expect(!auth.bootstrapOpen(), "offline administrator should persist across restart");
        expect(
            !std::filesystem::exists(offlineAuthFile.string() + ".sessions"),
            "offline bootstrap should remain session-free after restart");
    }

    {
        sisterd::AuthStore auth(authFile);
        expect(!auth.databaseBacked(), "file auth should remain the default backend");
        expect(auth.backendName() == "file", "file auth backend should be observable");
        expect(auth.bootstrapOpen(), "new store should accept bootstrap");

        const auto registered = auth.registerAdmin(
            "Equipe SisTer", "ADMIN@SISTER.LOCAL", "senha-segura-123");
        expect(registered.has_value(), "first administrator should be created");
        expect(registered->user.role == "admin", "bootstrap user should be administrator");
        expect(
            std::regex_match(
                registered->user.id,
                std::regex(
                    "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
                    "[89ab][0-9a-f]{3}-[0-9a-f]{12}$")),
            "new administrator should use a federable UUID");
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
        const auto researcher = auth.createUser(
            "Pesquisador Teste", "pesquisador@sister.local", "senha-de-equipe-123", "researcher");
        expect(researcher.has_value() && researcher->role == "researcher", "researcher role should be accepted");
        const auto projectLead = auth.createUser(
            "Coordenador Teste", "coordenador@sister.local", "senha-de-equipe-123", "project_lead");
        expect(projectLead.has_value() && projectLead->role == "project_lead", "project_lead role should be accepted");
        expect(auth.users().size() == 4, "user listing should include all created accounts");
        std::string dupErr;
        expect(
            !auth.createUser(
                "Duplicada", "pessoa@sister.local", "senha-de-equipe-456", "admin", &dupErr) &&
                dupErr == "E-mail já cadastrado.",
            "duplicate email should fail with specific error message");
        std::string shortPassErr;
        expect(
            !auth.createUser(
                "Senha Curta", "curta@sister.local", "12345", "user", &shortPassErr) &&
                shortPassErr == "A senha temporária deve ter no mínimo 12 caracteres.",
            "short password should fail with specific error message");
        const auto imported = auth.importUser(
            "2ad0c643-3129-4cf7-82c1-5d2afeeb8445",
            "Pessoa Migrada",
            "migrada@sister.local",
            "senha-migrada-123",
            "admin");
        expect(imported.has_value(), "explicit federated UUID should be imported");
        expect(
            imported->id == "2ad0c643-3129-4cf7-82c1-5d2afeeb8445",
            "imported UUID should be preserved");
        expect(
            !auth.importUser(
                "2ad0c643-3129-4cf7-82c1-5d2afeeb8445",
                "Outra",
                "outra@sister.local",
                "senha-migrada-456",
                "admin"),
            "duplicate imported UUID should fail");
        expect(
            !auth.login("admin@sister.local", "senha-incorreta"),
            "wrong password should fail");

        const auto login = auth.login("admin@sister.local", "senha-segura-123");
        expect(login.has_value(), "valid password should authenticate");
        persistentToken = login->token;
        expect(
            auth.userForToken(persistentToken).has_value(),
            "issued token should identify its user");

        // Test updateUser
        std::string updateErr;
        const auto updatedMember = auth.updateUser(
            member->id, "Pessoa Atualizada", "pessoa.nova@sister.local", "project_lead", "", &updateErr);
        expect(updatedMember.has_value() && updatedMember->name == "Pessoa Atualizada" &&
               updatedMember->email == "pessoa.nova@sister.local" && updatedMember->role == "project_lead",
               "updateUser should update name, email, and role");

        expect(
            !auth.updateUser(
                member->id, "Outro", "admin@sister.local", "project_lead", "", &updateErr) &&
                updateErr == "E-mail já cadastrado para outra pessoa.",
            "updateUser should fail when email conflicts with another user");

        // Demote imported user first so registered is the sole remaining admin
        auth.updateUser(imported->id, imported->name, imported->email, "user", "");

        expect(
            !auth.updateUser(
                registered->user.id, "Admin", "admin@sister.local", "user", "", &updateErr) &&
                updateErr == "Não é possível alterar o papel do único administrador do sistema.",
            "updateUser should prevent demoting the sole administrator when another admin is not available");

        // Test password update
        const auto passUpdated = auth.updateUser(
            member->id, "Pessoa Atualizada", "pessoa.nova@sister.local", "project_lead", "nova-senha-12345");
        expect(passUpdated.has_value(), "valid optional password should update credentials");
        expect(auth.login("pessoa.nova@sister.local", "nova-senha-12345").has_value(),
               "user should authenticate with new password");

        // Test deleteUser
        std::string deleteErr;
        expect(
            !auth.deleteUser(registered->user.id, registered->user.id, &deleteErr) &&
                deleteErr == "Você não pode excluir a sua própria conta logada.",
            "deleteUser should prevent self-deletion");

        expect(
            !auth.deleteUser(registered->user.id, member->id, &deleteErr) &&
                deleteErr == "Não é possível excluir o único administrador do sistema.",
            "deleteUser should prevent deleting sole administrator");

        expect(auth.deleteUser(member->id, registered->user.id, &deleteErr),
               "deleteUser should remove non-admin team member");
        expect(!auth.login("pessoa.nova@sister.local", "nova-senha-12345").has_value(),
               "deleted user credentials should no longer authenticate");
    }

    {
        sisterd::AuthStore auth(authFile);
        expect(!auth.bootstrapOpen(), "user should persist across restart");
        expect(
            auth.userForToken(persistentToken).has_value(),
            "active session should persist across restart");
        auth.logout(persistentToken);
        expect(
            auth.login("admin@sister.local", "senha-segura-123").has_value(),
            "persisted user should authenticate");
    }

    {
        sisterd::AuthStore auth(authFile);
        expect(
            !auth.userForToken(persistentToken),
            "revoked persisted session should remain revoked after restart");
    }

    std::filesystem::remove(authFile);
    std::filesystem::remove(authFile.string() + ".sessions");
    std::filesystem::remove(offlineAuthFile);
    std::filesystem::remove(offlineAuthFile.string() + ".sessions");
    std::cout << "sisterd_auth_tests ok\n";
    return 0;
}
