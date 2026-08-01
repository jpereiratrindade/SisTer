#pragma once

#include <filesystem>
#include <string>

namespace sisterd {
namespace api {

struct RouteResponse {
    int status_code;
    std::string reason_phrase;
    std::string content_type;
    std::string body;
};

RouteResponse getMaturityComponents(const std::filesystem::path& maturityRoot);
RouteResponse getMaturityCatalog(const std::filesystem::path& maturityRoot);
RouteResponse getQualityStatus(const std::filesystem::path& maturityRoot);

} // namespace api
} // namespace sisterd
