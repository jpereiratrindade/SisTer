#pragma once

#include <filesystem>
#include <string>
#include <optional>
#include "../auth.hpp"

namespace sisterd {
namespace api {

struct RouteResponse {
    int status_code;
    std::string reason_phrase;
    std::string content_type;
    std::string body;
};

RouteResponse getMaturityComponents(const std::optional<AuthUser>& actor, const std::filesystem::path& maturityRoot);
RouteResponse getMaturityCatalog(const std::optional<AuthUser>& actor, const std::filesystem::path& maturityRoot);
RouteResponse getQualityStatus(const std::optional<AuthUser>& actor, const std::filesystem::path& maturityRoot);

} // namespace api
} // namespace sisterd
