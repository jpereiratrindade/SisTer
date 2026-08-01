#include "connection_thread_pool.hpp"

#include <unistd.h>

#include <exception>
#include <utility>

namespace sisterd::runtime {

ConnectionThreadPool::ConnectionThreadPool(
    const std::size_t workerCount,
    const std::size_t queueLimit,
    Handler handler,
    ExceptionLogger exceptionLogger)
    : queueLimit_(queueLimit),
      handler_(std::move(handler)),
      exceptionLogger_(std::move(exceptionLogger)) {
    workers_.reserve(workerCount);
    for (std::size_t index = 0; index < workerCount; ++index) {
        workers_.emplace_back([this] { workerLoop(); });
    }
}

ConnectionThreadPool::~ConnectionThreadPool() {
    stop();
}

bool ConnectionThreadPool::submit(Job job) {
    std::lock_guard lock(mutex_);
    if (stopping_ || jobs_.size() >= queueLimit_) return false;
    jobs_.push_back(std::move(job));
    cv_.notify_one();
    return true;
}

void ConnectionThreadPool::stop() {
    {
        std::lock_guard lock(mutex_);
        if (stopping_) return;
        stopping_ = true;
    }
    cv_.notify_all();
    for (auto& worker : workers_) {
        if (worker.joinable()) worker.join();
    }
    workers_.clear();

    while (!jobs_.empty()) {
        if (jobs_.front().client >= 0) close(jobs_.front().client);
        jobs_.pop_front();
    }
}

void ConnectionThreadPool::workerLoop() {
    for (;;) {
        Job job;
        {
            std::unique_lock lock(mutex_);
            cv_.wait(lock, [this] { return stopping_ || !jobs_.empty(); });
            if (stopping_ && jobs_.empty()) return;
            job = std::move(jobs_.front());
            jobs_.pop_front();
        }
        try {
            handler_(job);
        } catch (const std::exception& error) {
            try { exceptionLogger_(error.what()); } catch (...) {}
        } catch (...) {
            try { exceptionLogger_("unknown exception"); } catch (...) {}
        }
        if (job.client >= 0) close(job.client);
    }
}

} // namespace sisterd::runtime
