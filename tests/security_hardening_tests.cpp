#include "content_length.hpp"
#include "connection_thread_pool.hpp"
#include "login_rate_limiter.hpp"

#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace {

void expect(const bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

void testContentLength() {
    using sisterd::http::ContentLengthStatus;
    constexpr std::size_t maximum = 16 * 1024 * 1024;
    const auto status = [](const std::string_view value) {
        return sisterd::http::parseContentLength(value, maximum).status;
    };
    expect(status("abc") == ContentLengthStatus::invalid, "letters must be invalid");
    expect(status("-1") == ContentLengthStatus::invalid, "negative length must be invalid");
    expect(status("+10") == ContentLengthStatus::invalid, "signed length must be invalid");
    expect(status("") == ContentLengthStatus::invalid, "empty length must be invalid");
    expect(status("1 0") == ContentLengthStatus::invalid, "internal spaces must be invalid");
    expect(status("999999999999999999999") == ContentLengthStatus::tooLarge,
           "overflow must map to payload too large");
    expect(status("16777217") == ContentLengthStatus::tooLarge,
           "value above maximum must be too large");
    const auto atLimit = sisterd::http::parseContentLength("16777216", maximum);
    expect(atLimit.status == ContentLengthStatus::valid && atLimit.value == maximum,
           "exact maximum must be accepted");
    expect(sisterd::http::parseContentLength("0", maximum).status == ContentLengthStatus::valid,
           "zero must be accepted");
}

sisterd::security::LoginRateLimiter::Limits limits(
    const std::size_t address,
    const std::size_t identity,
    const std::size_t pair,
    const std::size_t global,
    const std::size_t buckets = 4096) {
    return {address, identity, pair, global, buckets, std::chrono::seconds(60)};
}

void testRateLimiterScopes() {
    using Limiter = sisterd::security::LoginRateLimiter;
    const auto now = Limiter::Clock::time_point(std::chrono::seconds(1000));

    Limiter addressLimiter(limits(2, 100, 100, 100));
    expect(addressLimiter.checkAndRecord("192.0.2.1", "one@example.org", now).allowed,
           "first address attempt rejected");
    expect(addressLimiter.checkAndRecord("192.0.2.1", "two@example.org", now).allowed,
           "second address attempt rejected");
    const auto addressBlocked =
        addressLimiter.checkAndRecord("192.0.2.1", "three@example.org", now);
    expect(!addressBlocked.allowed && addressBlocked.scope == "address",
           "changing identity bypassed address limit");

    Limiter identityLimiter(limits(100, 2, 100, 100));
    expect(identityLimiter.checkAndRecord("192.0.2.1", "same@example.org", now).allowed,
           "first identity attempt rejected");
    expect(identityLimiter.checkAndRecord("192.0.2.2", "same@example.org", now).allowed,
           "second identity attempt rejected");
    const auto identityBlocked =
        identityLimiter.checkAndRecord("192.0.2.3", "same@example.org", now);
    expect(!identityBlocked.allowed && identityBlocked.scope == "identity",
           "changing address bypassed identity limit");

    Limiter pairLimiter(limits(100, 100, 2, 100));
    expect(pairLimiter.checkAndRecord("192.0.2.1", "same@example.org", now).allowed,
           "first pair attempt rejected");
    expect(pairLimiter.checkAndRecord("192.0.2.1", "same@example.org", now).allowed,
           "second pair attempt rejected");
    const auto pairBlocked =
        pairLimiter.checkAndRecord("192.0.2.1", "same@example.org", now);
    expect(!pairBlocked.allowed && pairBlocked.scope == "address_identity" &&
               pairBlocked.retryAfter.count() > 0,
           "pair limit or Retry-After missing");

    Limiter globalLimiter(limits(100, 100, 100, 2));
    expect(globalLimiter.checkAndRecord("192.0.2.1", "one@example.org", now).allowed,
           "first global attempt rejected");
    expect(globalLimiter.checkAndRecord("192.0.2.2", "two@example.org", now).allowed,
           "second global attempt rejected");
    const auto globalBlocked =
        globalLimiter.checkAndRecord("192.0.2.3", "three@example.org", now);
    expect(!globalBlocked.allowed && globalBlocked.scope == "global",
           "global limit not applied");
}

void testRateLimiterCapacityAndExpiry() {
    using Limiter = sisterd::security::LoginRateLimiter;
    const auto start = Limiter::Clock::time_point(std::chrono::seconds(2000));
    Limiter bounded(limits(100000, 100000, 100000, 100000, 64));
    Limiter::Decision last;
    for (std::size_t index = 0; index < 5000; ++index) {
        last = bounded.checkAndRecord(
            "198.51.100." + std::to_string(index),
            "identity-" + std::to_string(index) + "@example.org",
            start + std::chrono::milliseconds(index));
        expect(last.allowed, "capacity policy unexpectedly rejected an attempt");
    }
    expect(bounded.bucketCount() <= 64, "rate limiter exceeded bucket capacity");
    expect(last.evictions > 0, "bucket eviction metric was not recorded");

    bounded.pruneExpired(start + std::chrono::seconds(120));
    expect(bounded.bucketCount() == 0, "global expiry did not remove old buckets");
    expect(bounded.checkAndRecord(
               "203.0.113.1", "after-expiry@example.org",
               start + std::chrono::seconds(120)).allowed,
           "attempt after expiry should be allowed");
}

void testRateLimiterConcurrency() {
    using Limiter = sisterd::security::LoginRateLimiter;
    const auto now = Limiter::Clock::time_point(std::chrono::seconds(3000));
    Limiter limiter(limits(500, 500, 100, 500));
    std::atomic<int> allowed{0};
    std::atomic<int> rejected{0};
    std::vector<std::thread> threads;
    for (int index = 0; index < 200; ++index) {
        threads.emplace_back([&] {
            if (limiter.checkAndRecord("203.0.113.9", "parallel@example.org", now).allowed) {
                ++allowed;
            } else {
                ++rejected;
            }
        });
    }
    for (auto& thread : threads) thread.join();
    expect(allowed == 100 && rejected == 100,
           "concurrent rate limiting counters are inconsistent");
}

void testWorkerExceptionBarrier() {
    std::atomic<int> logged{0};
    std::atomic<int> completed{0};
    int standardPair[2] = {-1, -1};
    int unknownPair[2] = {-1, -1};
    int healthyPair[2] = {-1, -1};
    expect(socketpair(AF_UNIX, SOCK_STREAM, 0, standardPair) == 0, "socketpair failed");
    expect(socketpair(AF_UNIX, SOCK_STREAM, 0, unknownPair) == 0, "socketpair failed");
    expect(socketpair(AF_UNIX, SOCK_STREAM, 0, healthyPair) == 0, "socketpair failed");
    {
        sisterd::runtime::ConnectionThreadPool pool(
            1, 8,
            [&](const sisterd::runtime::ConnectionThreadPool::Job& job) {
                if (job.peer == "standard") throw std::runtime_error("deliberate test error\n");
                if (job.peer == "unknown") throw 7;
                ++completed;
            },
            [&](const std::string_view detail) {
                expect(detail.find('\n') == std::string_view::npos || detail == "deliberate test error\n",
                       "unexpected exception detail");
                ++logged;
            });
        expect(pool.submit({standardPair[0], "standard", "local"}), "standard job rejected");
        expect(pool.submit({unknownPair[0], "unknown", "local"}), "unknown job rejected");
        expect(pool.submit({healthyPair[0], "healthy", "local"}), "healthy job rejected");
        pool.stop();
    }
    char byte = 0;
    expect(recv(standardPair[1], &byte, 1, 0) == 0, "standard exception socket remained open");
    expect(recv(unknownPair[1], &byte, 1, 0) == 0, "unknown exception socket remained open");
    expect(recv(healthyPair[1], &byte, 1, 0) == 0, "completed job socket remained open");
    close(standardPair[1]);
    close(unknownPair[1]);
    close(healthyPair[1]);
    expect(logged == 2, "worker exception barrier did not log both exception types");
    expect(completed == 1, "worker did not continue after exceptions");
}

} // namespace

int main() {
    testContentLength();
    testRateLimiterScopes();
    testRateLimiterCapacityAndExpiry();
    testRateLimiterConcurrency();
    testWorkerExceptionBarrier();
    return 0;
}
