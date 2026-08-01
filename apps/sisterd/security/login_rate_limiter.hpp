#pragma once

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <mutex>
#include <string>
#include <string_view>
#include <unordered_map>

namespace sisterd::security {

class LoginRateLimiter {
public:
    using Clock = std::chrono::steady_clock;

    struct Limits {
        std::size_t perAddress = 32;
        std::size_t perIdentity = 16;
        std::size_t perAddressAndIdentity = 8;
        std::size_t global = 512;
        std::size_t maximumBuckets = 4096;
        std::chrono::seconds window{300};
    };

    struct Decision {
        bool allowed = false;
        std::chrono::seconds retryAfter{0};
        std::string scope;
        std::size_t buckets = 0;
        std::uint64_t rejections = 0;
        std::uint64_t evictions = 0;
    };

    LoginRateLimiter();
    explicit LoginRateLimiter(Limits limits);

    [[nodiscard]] Decision checkAndRecord(
        std::string_view address,
        std::string_view normalizedIdentity,
        Clock::time_point now = Clock::now());
    void pruneExpired(Clock::time_point now = Clock::now());
    [[nodiscard]] std::size_t bucketCount() const;

private:
    struct Bucket {
        std::deque<Clock::time_point> attempts;
        Clock::time_point lastAccess{};
    };

    void pruneExpiredUnlocked(Clock::time_point now);
    void ensureCapacityUnlocked(
        const std::string* keys,
        std::size_t keyCount,
        Clock::time_point now);

    Limits limits_;
    mutable std::mutex mutex_;
    std::unordered_map<std::string, Bucket> buckets_;
    std::uint64_t rejections_ = 0;
    std::uint64_t evictions_ = 0;
};

} // namespace sisterd::security
