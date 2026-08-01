#include "content_length.hpp"

#include <limits>

namespace sisterd::http {

ContentLengthResult parseContentLength(
    const std::string_view value,
    const std::size_t maximum) noexcept {
    if (value.empty()) return {ContentLengthStatus::invalid, 0};

    std::size_t parsed = 0;
    for (const unsigned char character : value) {
        if (character < '0' || character > '9') {
            return {ContentLengthStatus::invalid, 0};
        }
        const auto digit = static_cast<std::size_t>(character - '0');
        if (parsed > (std::numeric_limits<std::size_t>::max() - digit) / 10) {
            return {ContentLengthStatus::tooLarge, 0};
        }
        parsed = parsed * 10 + digit;
        if (parsed > maximum) return {ContentLengthStatus::tooLarge, 0};
    }
    return {ContentLengthStatus::valid, parsed};
}

} // namespace sisterd::http
