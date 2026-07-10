#include "sister/contract.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
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
              << "  sisterctl validate-manifest <manifest.json>\n";
}

} // namespace

int main(int argc, char** argv) {
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
