#include "login_rate_limiter.hpp"

#include <algorithm>
#include <array>
#include <stdexcept>

namespace sisterd::security {
namespace {

constexpr std::string_view globalKey = "global";

} // namespace

LoginRateLimiter::LoginRateLimiter() : LoginRateLimiter(Limits{}) {}

LoginRateLimiter::LoginRateLimiter(Limits limits) : limits_(limits) {
    if (limits_.perAddress == 0 || limits_.perIdentity == 0 ||
        limits_.perAddressAndIdentity == 0 || limits_.global == 0 ||
        limits_.maximumBuckets < 4 || limits_.window <= std::chrono::seconds::zero()) {
        throw std::invalid_argument("invalid login rate limiter configuration");
    }
}

LoginRateLimiter::Decision LoginRateLimiter::checkAndRecord(
    const std::string_view address,
    const std::string_view normalizedIdentity,
    const Clock::time_point now) {
    if (address.empty() || normalizedIdentity.empty()) {
        throw std::invalid_argument("login rate limit keys must not be empty");
    }

    const std::array<std::string, 4> keys{
        std::string(globalKey),
        "address:" + std::string(address),
        "identity:" + std::string(normalizedIdentity),
        "pair:" + std::string(address) + ':' + std::string(normalizedIdentity),
    };
    const std::array<std::size_t, 4> limits{
        limits_.global,
        limits_.perAddress,
        limits_.perIdentity,
        limits_.perAddressAndIdentity,
    };
    const std::array<std::string_view, 4> scopes{
        "global", "address", "identity", "address_identity"};

    std::lock_guard lock(mutex_);
    pruneExpiredUnlocked(now);
    for (std::size_t index = 0; index < keys.size(); ++index) {
        const auto found = buckets_.find(keys[index]);
        if (found == buckets_.end() || found->second.attempts.size() < limits[index]) continue;
        ++rejections_;
        const auto retryAt = found->second.attempts.front() + limits_.window;
        const auto retryAfter = std::max(
            std::chrono::seconds(1),
            std::chrono::duration_cast<std::chrono::seconds>(retryAt - now) +
                std::chrono::seconds(1));
        return {
            false, retryAfter, std::string(scopes[index]), buckets_.size(),
            rejections_, evictions_};
    }

    ensureCapacityUnlocked(keys.data(), keys.size(), now);
    for (const auto& key : keys) {
        auto& bucket = buckets_[key];
        bucket.attempts.push_back(now);
        bucket.lastAccess = now;
    }
    return {true, {}, {}, buckets_.size(), rejections_, evictions_};
}

void LoginRateLimiter::pruneExpired(const Clock::time_point now) {
    std::lock_guard lock(mutex_);
    pruneExpiredUnlocked(now);
}

std::size_t LoginRateLimiter::bucketCount() const {
    std::lock_guard lock(mutex_);
    return buckets_.size();
}

void LoginRateLimiter::pruneExpiredUnlocked(const Clock::time_point now) {
    const auto cutoff = now - limits_.window;
    for (auto iterator = buckets_.begin(); iterator != buckets_.end();) {
        auto& attempts = iterator->second.attempts;
        while (!attempts.empty() && attempts.front() <= cutoff) attempts.pop_front();
        if (attempts.empty()) iterator = buckets_.erase(iterator);
        else ++iterator;
    }
}

void LoginRateLimiter::ensureCapacityUnlocked(
    const std::string* keys,
    const std::size_t keyCount,
    const Clock::time_point now) {
    std::size_t missing = 0;
    for (std::size_t index = 0; index < keyCount; ++index) {
        if (!buckets_.contains(keys[index])) ++missing;
    }
    while (buckets_.size() + missing > limits_.maximumBuckets) {
        auto oldest = buckets_.end();
        for (auto iterator = buckets_.begin(); iterator != buckets_.end(); ++iterator) {
            if (iterator->first == globalKey ||
                std::find(keys, keys + keyCount, iterator->first) != keys + keyCount) continue;
            if (oldest == buckets_.end() || iterator->second.lastAccess < oldest->second.lastAccess) {
                oldest = iterator;
            }
        }
        if (oldest == buckets_.end()) {
            throw std::runtime_error("login rate limiter bucket capacity exhausted");
        }
        buckets_.erase(oldest);
        ++evictions_;
    }
    (void)now;
}

} // namespace sisterd::security
