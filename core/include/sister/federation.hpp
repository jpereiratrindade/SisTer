#pragma once

#include <optional>
#include <map>
#include <string>
#include <utility>
#include <variant>
#include <vector>
#include <algorithm>

namespace sister {

struct FederationError final {
    std::string field;
    std::string message;
};

template <typename Tag>
class FederationId final {
public:
    static std::variant<FederationId, FederationError> fromString(std::string value) {
        if (value.empty()) return FederationError{"id", "identifier must not be empty"};
        return FederationId{std::move(value)};
    }
    [[nodiscard]] const std::string& value() const noexcept { return value_; }
    friend bool operator==(const FederationId&, const FederationId&) = default;
private:
    explicit FederationId(std::string value) : value_(std::move(value)) {}
    std::string value_;
};

struct SystemIdTag {};
struct SystemVersionTag {};
struct CapabilityIdTag {};
struct CapabilityVersionTag {};
struct OwnerIdTag {};

using FederatedSystemId = FederationId<SystemIdTag>;
using SystemVersion = FederationId<SystemVersionTag>;
using CapabilityId = FederationId<CapabilityIdTag>;
using CapabilityVersion = FederationId<CapabilityVersionTag>;
using OwnerId = FederationId<OwnerIdTag>;

enum class OperationalStatus { active, degraded, inactive, suspended };
enum class Maturity { experimental, pre_alpha, alpha, beta, production };

struct CapabilityDeclaration final {
    CapabilityId id;
    CapabilityVersion version;
    std::string contract;
    friend bool operator==(const CapabilityDeclaration&, const CapabilityDeclaration&) = default;
};

struct GovernedSystemManifest final {
    FederatedSystemId id;
    SystemVersion version;
    OwnerId owner;
    std::vector<CapabilityDeclaration> capabilities;
    OperationalStatus operational_status = OperationalStatus::inactive;
    Maturity maturity = Maturity::experimental;
};

class GovernedSystemRegistry final {
public:
    std::variant<std::monostate, FederationError>
    registerSystem(GovernedSystemManifest manifest) {
        if (manifest.id.value().empty()) return FederationError{"id", "system identity is required"};
        if (manifest.version.value().empty()) return FederationError{"version", "system version is required"};
        if (manifest.owner.value().empty()) return FederationError{"owner", "owner is required"};
        if (manifest.capabilities.empty()) return FederationError{"capabilities", "at least one capability is required"};
        const auto key = manifest.id.value();
        if (systems_.contains(key)) {
            return systems_.at(key).version == manifest.version
                && systems_.at(key).owner == manifest.owner
                && systems_.at(key).capabilities == manifest.capabilities
                && systems_.at(key).operational_status == manifest.operational_status
                && systems_.at(key).maturity == manifest.maturity
                ? std::variant<std::monostate, FederationError>{std::monostate{}}
                : std::variant<std::monostate, FederationError>{FederationError{"id", "conflicting system registration"}};
        }
        for (std::size_t i = 0; i < manifest.capabilities.size(); ++i) {
            if (manifest.capabilities[i].version.value().empty() || manifest.capabilities[i].contract.empty()) {
                return FederationError{"capabilities", "capability version and contract are required"};
            }
            for (std::size_t j = i + 1; j < manifest.capabilities.size(); ++j) {
                if (manifest.capabilities[i].id == manifest.capabilities[j].id) {
                    return FederationError{"capabilities", "duplicate capability identity"};
                }
            }
        }
        systems_.emplace(key, std::move(manifest));
        return std::monostate{};
    }

    std::variant<std::monostate, FederationError>
    updateOperationalStatus(const FederatedSystemId& id, OperationalStatus status) {
        const auto it = systems_.find(id.value());
        if (it == systems_.end()) return FederationError{"id", "system is not registered"};
        it->second.operational_status = status;
        return std::monostate{};
    }

    std::variant<std::monostate, FederationError>
    updateMaturity(const FederatedSystemId& id, Maturity maturity) {
        const auto it = systems_.find(id.value());
        if (it == systems_.end()) return FederationError{"id", "system is not registered"};
        it->second.maturity = maturity;
        return std::monostate{};
    }

    [[nodiscard]] std::optional<GovernedSystemManifest> find(const FederatedSystemId& id) const {
        const auto it = systems_.find(id.value());
        return it == systems_.end() ? std::nullopt : std::optional{it->second};
    }

    [[nodiscard]] std::vector<GovernedSystemManifest> list() const {
        std::vector<GovernedSystemManifest> result;
        result.reserve(systems_.size());
        for (const auto& [_, system] : systems_) result.push_back(system);
        return result;
    }

private:
    std::map<std::string, GovernedSystemManifest> systems_;
};

} // namespace sister
