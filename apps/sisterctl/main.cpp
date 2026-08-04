#include "sister/contract.hpp"
#include "auth.hpp"

#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <termios.h>
#include <unistd.h>

namespace {

std::string readFile(const std::filesystem::path& path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("could not open file: " + path.string());
    }
    std::ostringstream buffer;
    buffer << in.rdbuf();
    return buffer.str();
}

void usage() {
    std::cout << "usage:\n"
              << "  sisterctl validate-manifest <manifest.json>\n"
              << "  sisterctl db-check\n"
              << "  sisterctl db-migrate [migration.sql]\n"
              << "  sisterctl participation propose <contract.json> [--json]\n"
              << "  sisterctl participation show <participation_id> [--json]\n"
              << "  sisterctl auth bootstrap-admin <name> <email>\n"
              << "  sisterctl auth-import-user <uuid> <name> <email> <role>\n";
}

int runScript(const std::string& command) {
    const int rc = std::system(command.c_str());
    if (rc != 0) {
        std::cerr << "command failed: " << command << '\n';
        return 1;
    }
    return 0;
}

std::string shellQuote(const std::string& value);

int runParticipation(const std::string& operation, const std::string& value, bool asJson) {
    return runScript("python3 ./scripts/participation_client.py " + shellQuote(operation) + " " + shellQuote(value) + (asJson ? " --json" : ""));
}

std::string shellQuote(const std::string& value) {
    std::string quoted = "'";
    for (const char c : value) {
        if (c == '\'') {
            quoted += "'\\''";
        } else {
            quoted += c;
        }
    }
    quoted += "'";
    return quoted;
}

class TerminalEchoGuard {
public:
    TerminalEchoGuard() {
        if (!isatty(STDIN_FILENO) || tcgetattr(STDIN_FILENO, &original_) != 0) {
            throw std::runtime_error("password input requires an interactive terminal");
        }
        auto hidden = original_;
        hidden.c_lflag &= static_cast<tcflag_t>(~ECHO);
        if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &hidden) != 0) {
            throw std::runtime_error("could not hide terminal input");
        }
        active_ = true;
    }

    ~TerminalEchoGuard() {
        if (active_) tcsetattr(STDIN_FILENO, TCSAFLUSH, &original_);
    }

    TerminalEchoGuard(const TerminalEchoGuard&) = delete;
    TerminalEchoGuard& operator=(const TerminalEchoGuard&) = delete;

private:
    termios original_ {};
    bool active_ = false;
};

std::string readHidden(const std::string& prompt) {
    std::cout << prompt << std::flush;
    std::string value;
    {
        TerminalEchoGuard guard;
        std::getline(std::cin, value);
    }
    std::cout << '\n';
    return value;
}

} // namespace

int main(int argc, char** argv) {
    if (argc >= 2 && std::string(argv[1]) == "participation") {
        if ((argc != 4 && argc != 5) || (std::string(argv[2]) != "propose" && std::string(argv[2]) != "show") || (argc == 5 && std::string(argv[4]) != "--json")) {
            usage();
            return 2;
        }
        return runParticipation(argv[2], argv[3], argc == 5);
    }
    if (argc >= 3 && std::string(argv[1]) == "auth" &&
        std::string(argv[2]) == "bootstrap-admin") {
        if (argc != 5) {
            usage();
            return 2;
        }
        try {
            const char* configuredPath = std::getenv("SISTER_AUTH_FILE");
            if (configuredPath == nullptr || std::string_view(configuredPath).empty()) {
                throw std::runtime_error(
                    "SISTER_AUTH_FILE must be explicitly configured for administrator bootstrap");
            }
            const std::filesystem::path authPath = configuredPath;
            if (!authPath.is_absolute()) {
                throw std::runtime_error(
                    "SISTER_AUTH_FILE must be an absolute path for administrator bootstrap");
            }
            const auto password = readHidden("Nova senha administrativa: ");
            const auto confirmation = readHidden("Confirme a senha: ");
            if (password != confirmation) {
                std::cerr << "password confirmation does not match\n";
                return 1;
            }
            sisterd::AuthStore auth(authPath);
            const auto registered = auth.bootstrapAdmin(argv[3], argv[4], password);
            if (!registered) {
                std::cerr << "administrator bootstrap is closed or the supplied data is invalid\n";
                return 1;
            }
            std::cout << "administrator created: " << registered->email << '\n';
            return 0;
        } catch (const std::exception& ex) {
            std::cerr << "error: " << ex.what() << '\n';
            return 1;
        }
    }

    if (argc >= 2 && std::string(argv[1]) == "auth-import-user") {
        if (argc != 6) {
            usage();
            return 2;
        }
        try {
            const auto password = readHidden("Nova senha: ");
            const auto confirmation = readHidden("Confirme a senha: ");
            if (password != confirmation) {
                std::cerr << "password confirmation does not match\n";
                return 1;
            }
            const char* configuredPath = std::getenv("SISTER_AUTH_FILE");
            const std::filesystem::path authPath =
                configuredPath != nullptr ? configuredPath : ".run/auth-users.tsv";
            sisterd::AuthStore auth(authPath);
            const auto imported =
                auth.importUser(argv[2], argv[3], argv[4], password, argv[5]);
            if (!imported) {
                std::cerr << "could not import user; verify UUID, fields, role "
                             "or duplicate identity\n";
                return 1;
            }
            std::cout << "user imported: " << imported->email << '\n';
            return 0;
        } catch (const std::exception& ex) {
            std::cerr << "error: " << ex.what() << '\n';
            return 1;
        }
    }

    if (argc >= 2 && std::string(argv[1]) == "db-check") {
        if (argc != 2) {
            usage();
            return 2;
        }
        return runScript("./scripts/dev/db_check.sh");
    }

    if (argc >= 2 && std::string(argv[1]) == "db-migrate") {
        if (argc > 3) {
            usage();
            return 2;
        }
        const std::string migration = argc == 3 ? argv[2] : "storage/migrations/001_init.sql";
        return runScript("./scripts/dev/db_migrate.sh " + shellQuote(migration));
    }

    if (argc != 3 || std::string(argv[1]) != "validate-manifest") {
        usage();
        return 2;
    }

    try {
        const auto json = readFile(argv[2]);
        const auto manifest = sister::parseSystemManifestJson(json);
        const auto validation = sister::validateSystemManifest(manifest);
        std::cout << sister::to_string(validation) << '\n';
        return validation.ok ? 0 : 1;
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << '\n';
        return 1;
    }
}
