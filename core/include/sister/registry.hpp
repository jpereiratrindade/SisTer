#pragma once

#include "sister/contract.hpp"

#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace sister {

class SystemRegistry {
public:
    ValidationResult registerSystem(SystemManifest manifest);
    [[nodiscard]] std::optional<SystemManifest> findById(const std::string& system_id) const;
    [[nodiscard]] std::vector<SystemManifest> list() const;

private:
    std::unordered_map<std::string, SystemManifest> systems_;
};

} // namespace sister
