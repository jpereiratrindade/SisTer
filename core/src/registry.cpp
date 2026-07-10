#include "sister/registry.hpp"

namespace sister {

ValidationResult SystemRegistry::registerSystem(SystemManifest manifest) {
    auto validation = validateSystemManifest(manifest);
    if (!validation.ok) {
        return validation;
    }

    systems_[manifest.system_id] = std::move(manifest);
    return validation;
}

std::optional<SystemManifest> SystemRegistry::findById(const std::string& system_id) const {
    const auto it = systems_.find(system_id);
    if (it == systems_.end()) {
        return std::nullopt;
    }
    return it->second;
}

std::vector<SystemManifest> SystemRegistry::list() const {
    std::vector<SystemManifest> systems;
    systems.reserve(systems_.size());
    for (const auto& [_, manifest] : systems_) {
        systems.push_back(manifest);
    }
    return systems;
}

} // namespace sister
