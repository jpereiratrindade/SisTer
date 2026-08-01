#pragma once

#include <filesystem>
#include <string>

namespace sisterd::identity {

struct SigningKey {
    std::string kid;
    std::string privateKeyPem;
};

class KeyProvider {
public:
    virtual ~KeyProvider() = default;
    [[nodiscard]] virtual SigningKey currentSigningKey() const = 0;
};

class FileKeyProvider final : public KeyProvider {
public:
    FileKeyProvider(std::filesystem::path privateKeyPath, std::string kid);
    [[nodiscard]] SigningKey currentSigningKey() const override;

private:
    std::filesystem::path privateKeyPath_;
    std::string kid_;
};

} // namespace sisterd::identity
