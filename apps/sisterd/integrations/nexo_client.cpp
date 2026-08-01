#include "nexo_client.hpp"

#include "../identity/internal_assertion.hpp"

#include <arpa/inet.h>
#include <cerrno>
#include <fcntl.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <chrono>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <utility>

namespace sisterd::integrations {
namespace {

constexpr std::size_t kMaximumResponseBytes = 8 * 1024 * 1024;

class UniqueFd {
public:
    explicit UniqueFd(int fd = -1) noexcept : fd_(fd) {}
    ~UniqueFd() { if (fd_ >= 0) close(fd_); }
    UniqueFd(const UniqueFd&) = delete;
    UniqueFd& operator=(const UniqueFd&) = delete;
    UniqueFd(UniqueFd&& other) noexcept : fd_(std::exchange(other.fd_, -1)) {}
    [[nodiscard]] int get() const noexcept { return fd_; }
private:
    int fd_;
};

std::string safeHeader(std::string_view value, std::size_t maximum = 4096) {
    if (value.empty() || value.size() > maximum ||
        value.find('\r') != std::string_view::npos || value.find('\n') != std::string_view::npos ||
        std::any_of(value.begin(), value.end(), [](unsigned char character) {
            return character < 0x20 || character == 0x7f;
        })) {
        throw std::runtime_error("unsafe Nexo request header");
    }
    return std::string(value);
}

void configureTimeouts(int socket, int timeoutMilliseconds) {
    timeval timeout{};
    timeout.tv_sec = std::max(1, (timeoutMilliseconds + 999) / 1000);
    if (setsockopt(socket, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0 ||
        setsockopt(socket, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout)) < 0) {
        throw std::runtime_error("cannot configure Nexo socket timeouts");
    }
}

UniqueFd connectLoopback(std::uint16_t port, int timeoutMilliseconds) {
    UniqueFd socketHandle(socket(AF_INET, SOCK_STREAM, 0));
    if (socketHandle.get() < 0) throw std::runtime_error("cannot create Nexo client socket");
    const int originalFlags = fcntl(socketHandle.get(), F_GETFL, 0);
    if (originalFlags < 0 || fcntl(socketHandle.get(), F_SETFL, originalFlags | O_NONBLOCK) < 0) {
        throw std::runtime_error("cannot configure Nexo client socket");
    }
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    const int result = connect(
        socketHandle.get(), reinterpret_cast<sockaddr*>(&address), sizeof(address));
    if (result < 0 && errno != EINPROGRESS) throw std::runtime_error("Nexo is unavailable");
    if (result < 0) {
        pollfd descriptor{socketHandle.get(), POLLOUT, 0};
        int ready;
        do { ready = poll(&descriptor, 1, timeoutMilliseconds); }
        while (ready < 0 && errno == EINTR);
        if (ready <= 0) throw std::runtime_error("Nexo connection timeout");
        int socketError = 0;
        socklen_t socketErrorSize = sizeof(socketError);
        if (getsockopt(
                socketHandle.get(), SOL_SOCKET, SO_ERROR, &socketError, &socketErrorSize) < 0 ||
            socketError != 0) {
            throw std::runtime_error("Nexo connection failed");
        }
    }
    if (fcntl(socketHandle.get(), F_SETFL, originalFlags) < 0) {
        throw std::runtime_error("cannot restore Nexo client socket mode");
    }
    configureTimeouts(socketHandle.get(), timeoutMilliseconds);
    return socketHandle;
}

void sendAll(int socket, std::string_view value) {
    std::size_t sent = 0;
    while (sent < value.size()) {
#ifdef MSG_NOSIGNAL
        const auto count = send(socket, value.data() + sent, value.size() - sent, MSG_NOSIGNAL);
#else
        const auto count = send(socket, value.data() + sent, value.size() - sent, 0);
#endif
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) throw std::runtime_error("cannot send request to Nexo");
        sent += static_cast<std::size_t>(count);
    }
}

} // namespace

NexoClient::NexoClient(IntegrationClientConfig config) : config_(std::move(config)) {
    if (config_.port == 0 || config_.timeoutMilliseconds < 100 ||
        config_.assertionTtl <= std::chrono::seconds::zero() ||
        config_.assertionTtl > std::chrono::seconds(300)) {
        throw std::runtime_error("invalid Nexo client configuration");
    }
}

std::string NexoClient::execute(const AuthorizedIntegrationRequest& request) const {
    if (request.path.empty() || request.path.front() != '/' ||
        request.path.find('\r') != std::string::npos || request.path.find('\n') != std::string::npos ||
        request.query.find('\r') != std::string::npos || request.query.find('\n') != std::string::npos) {
        throw std::runtime_error("invalid Nexo request path");
    }

    const auto now = std::chrono::system_clock::now();
    const auto issuedAt = std::chrono::duration_cast<std::chrono::seconds>(
        now.time_since_epoch()).count();
    identity::InternalAssertionClaims claims{
        "sisterd",
        request.subject,
        "sister_nexo",
        {request.capability},
        request.purpose,
        issuedAt,
        issuedAt + config_.assertionTtl.count(),
        identity::randomAssertionId(),
        request.requestId,
    };
    auto provider = std::make_shared<identity::FileKeyProvider>(
        config_.privateKeyFile, config_.keyId);
    const identity::AssertionSigner signer(provider);
    const auto assertion = signer.sign(claims);

    auto upstream = connectLoopback(config_.port, config_.timeoutMilliseconds);
    std::ostringstream outbound;
    outbound << request.method << ' ' << request.path << request.query << " HTTP/1.1\r\n"
             << "Host: 127.0.0.1:" << config_.port << "\r\n"
             << "Authorization: Sister-Assertion " << safeHeader(assertion, 16 * 1024) << "\r\n"
             << "X-Request-ID: " << safeHeader(request.requestId, 128) << "\r\n";
    if (!request.contentType.empty()) {
        outbound << "Content-Type: " << safeHeader(request.contentType) << "\r\n";
    }
    if (!request.accept.empty()) outbound << "Accept: " << safeHeader(request.accept) << "\r\n";
    if (!request.body.empty()) outbound << "Content-Length: " << request.body.size() << "\r\n";
    outbound << "Connection: close\r\n\r\n" << request.body;
    sendAll(upstream.get(), outbound.str());

    std::string response;
    response.reserve(16 * 1024);
    char buffer[16 * 1024];
    for (;;) {
        const auto count = recv(upstream.get(), buffer, sizeof(buffer), 0);
        if (count == 0) break;
        if (count < 0) {
            if (errno == EINTR) continue;
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                throw std::runtime_error("Nexo response timeout");
            }
            throw std::runtime_error("cannot read response from Nexo");
        }
        if (response.size() + static_cast<std::size_t>(count) > kMaximumResponseBytes) {
            throw std::runtime_error("Nexo response exceeds limit");
        }
        response.append(buffer, static_cast<std::size_t>(count));
    }
    if (!response.starts_with("HTTP/1.") || response.find("\r\n\r\n") == std::string::npos) {
        throw std::runtime_error("invalid response from Nexo");
    }
    return response;
}

} // namespace sisterd::integrations
