#pragma once

#include <condition_variable>
#include <cstddef>
#include <deque>
#include <functional>
#include <mutex>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

namespace sisterd::runtime {

class ConnectionThreadPool {
public:
    struct Job {
        int client = -1;
        std::string peer;
        std::string remoteAddress;
    };

    using Handler = std::function<void(const Job&)>;
    using ExceptionLogger = std::function<void(std::string_view)>;

    ConnectionThreadPool(
        std::size_t workerCount,
        std::size_t queueLimit,
        Handler handler,
        ExceptionLogger exceptionLogger);
    ~ConnectionThreadPool();

    ConnectionThreadPool(const ConnectionThreadPool&) = delete;
    ConnectionThreadPool& operator=(const ConnectionThreadPool&) = delete;

    bool submit(Job job);
    void stop();

private:
    void workerLoop();

    std::size_t queueLimit_;
    Handler handler_;
    ExceptionLogger exceptionLogger_;
    std::mutex mutex_;
    std::condition_variable cv_;
    std::deque<Job> jobs_;
    std::vector<std::thread> workers_;
    bool stopping_ = false;
};

} // namespace sisterd::runtime
