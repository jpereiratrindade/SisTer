#pragma once

#include <cstddef>
#include <string_view>

namespace sisterd::http {

enum class ContentLengthStatus {
    valid,
    invalid,
    tooLarge,
};

struct ContentLengthResult {
    ContentLengthStatus status = ContentLengthStatus::invalid;
    std::size_t value = 0;
};

[[nodiscard]] ContentLengthResult parseContentLength(
    std::string_view value,
    std::size_t maximum) noexcept;

} // namespace sisterd::http
