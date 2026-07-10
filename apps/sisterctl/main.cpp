#include "sister/contract.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <cstdlib>
#include <string>

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
              << "  sisterctl db-migrate [migration.sql]\n";
}

int runScript(const std::string& command) {
    const int rc = std::system(command.c_str());
    if (rc != 0) {
        std::cerr << "command failed: " << command << '\n';
        return 1;
    }
    return 0;
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

} // namespace

int main(int argc, char** argv) {
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
