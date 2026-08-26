#include "ecosystem/ecosystem_view.hpp"

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <array>
#include <cerrno>
#include <charconv>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <sstream>

namespace sister::ecosystem {

namespace {

struct ScopedFd {
    int fd = -1;
    ScopedFd() = default;
    explicit ScopedFd(int f) : fd(f) {}
    ~ScopedFd() {
        if (fd >= 0) ::close(fd);
    }
    ScopedFd(const ScopedFd&) = delete;
    ScopedFd& operator=(const ScopedFd&) = delete;
    ScopedFd(ScopedFd&& other) noexcept : fd(other.fd) { other.fd = -1; }
    ScopedFd& operator=(ScopedFd&& other) noexcept {
        if (this != &other) {
            if (fd >= 0) ::close(fd);
            fd = other.fd;
            other.fd = -1;
        }
        return *this;
    }
    [[nodiscard]] int get() const noexcept { return fd; }
};

int statusFromRawHttpResponse(std::string_view response) noexcept {
    const auto firstSpace = response.find(' ');
    if (firstSpace == std::string_view::npos || firstSpace + 4 > response.size()) return 502;
    int status = 0;
    const auto [pointer, error] = std::from_chars(
        response.data() + firstSpace + 1,
        response.data() + std::min(response.size(), firstSpace + 4),
        status);
    if (error != std::errc{} || pointer != response.data() + firstSpace + 4) return 502;
    return status;
}

ScopedFd connectLoopback(uint16_t port, int timeoutMilliseconds) {
    ScopedFd sock(::socket(AF_INET, SOCK_STREAM, 0));
    if (sock.get() < 0) {
        throw std::runtime_error("socket_creation_failed");
    }

    const int originalFlags = fcntl(sock.get(), F_GETFL, 0);
    if (originalFlags < 0 || fcntl(sock.get(), F_SETFL, originalFlags | O_NONBLOCK) < 0) {
        throw std::runtime_error("set_nonblocking_failed");
    }

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    if (::inet_pton(AF_INET, "127.0.0.1", &address.sin_addr) != 1) {
        throw std::runtime_error("inet_pton_failed");
    }

    const int result = ::connect(sock.get(), reinterpret_cast<sockaddr*>(&address), sizeof(address));
    if (result < 0) {
        if (errno != EINPROGRESS) {
            throw std::runtime_error("connect_failed");
        }
        pollfd pfd{};
        pfd.fd = sock.get();
        pfd.events = POLLOUT;
        int pollResult = 0;
        do {
            pollResult = ::poll(&pfd, 1, timeoutMilliseconds);
        } while (pollResult < 0 && errno == EINTR);

        if (pollResult <= 0) {
            throw std::runtime_error(pollResult == 0 ? "connect_timeout" : "poll_error");
        }
        int error = 0;
        socklen_t len = sizeof(error);
        if (::getsockopt(sock.get(), SOL_SOCKET, SO_ERROR, &error, &len) < 0 || error != 0) {
            throw std::runtime_error("connect_refused");
        }
    }

    if (fcntl(sock.get(), F_SETFL, originalFlags) < 0) {
        throw std::runtime_error("restore_flags_failed");
    }

    timeval tv{};
    tv.tv_sec = std::max(1, (timeoutMilliseconds + 999) / 1000);
    tv.tv_usec = 0;
    setsockopt(sock.get(), SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(sock.get(), SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    return sock;
}

bool sendAll(int fd, std::string_view data) noexcept {
    std::size_t totalSent = 0;
    while (totalSent < data.size()) {
        const auto sent = ::send(fd, data.data() + totalSent, data.size() - totalSent, MSG_NOSIGNAL);
        if (sent <= 0) {
            if (sent < 0 && errno == EINTR) continue;
            return false;
        }
        totalSent += static_cast<std::size_t>(sent);
    }
    return true;
}

std::vector<std::string_view> splitByTab(std::string_view line) {
    std::vector<std::string_view> tokens;
    std::size_t start = 0;
    while (start <= line.size()) {
        const auto tab = line.find('\t', start);
        if (tab == std::string_view::npos) {
            tokens.push_back(line.substr(start));
            break;
        }
        tokens.push_back(line.substr(start, tab - start));
        start = tab + 1;
    }
    return tokens;
}

std::string_view trimCarriageReturn(std::string_view line) {
    if (!line.empty() && line.back() == '\r') {
        line.remove_suffix(1);
    }
    return line;
}

} // namespace

std::string jsonEscape(std::string_view value) {
    std::string result;
    result.reserve(value.size() + 16);
    for (const char c : value) {
        switch (c) {
            case '"': result += "\\\""; break;
            case '\\': result += "\\\\"; break;
            case '\b': result += "\\b"; break;
            case '\f': result += "\\f"; break;
            case '\n': result += "\\n"; break;
            case '\r': result += "\\r"; break;
            case '\t': result += "\\t"; break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    char buf[8];
                    std::snprintf(buf, sizeof(buf), "\\u%04x", static_cast<unsigned char>(c));
                    result += buf;
                } else {
                    result += c;
                }
                break;
        }
    }
    return result;
}

EcosystemView parseProjection(std::string_view content) {
    EcosystemView view;
    std::size_t lineStart = 0;

    while (lineStart < content.size()) {
        auto lineEnd = content.find('\n', lineStart);
        if (lineEnd == std::string_view::npos) {
            lineEnd = content.size();
        }

        std::string_view line = trimCarriageReturn(content.substr(lineStart, lineEnd - lineStart));
        lineStart = lineEnd + 1;

        if (line.empty() || line.front() == '#') continue;

        const auto tokens = splitByTab(line);
        if (tokens.empty()) continue;

        if (tokens[0] == "META") {
            if (tokens.size() > 1) view.compositionId = std::string(tokens[1]);
            if (tokens.size() > 2) view.deploymentId = std::string(tokens[2]);
            if (tokens.size() > 3 && !tokens[3].empty()) {
                view.deploymentStatus = std::string(tokens[3]);
            }
        } else if (tokens[0] == "PARTICIPANT") {
            // tokens: PARTICIPANT, component_id, system_id, transport, listen, port, health_path, gateway_host
            EcosystemParticipant p;
            if (tokens.size() > 1) p.componentId = std::string(tokens[1]);
            if (tokens.size() > 2) p.systemId = std::string(tokens[2]);
            if (tokens.size() > 3) p.runtime.transport = std::string(tokens[3]);
            if (tokens.size() > 4) p.runtime.listen = std::string(tokens[4]);
            if (tokens.size() > 5 && !tokens[5].empty()) {
                int parsedPort = 0;
                const auto [ptr, ec] = std::from_chars(tokens[5].data(), tokens[5].data() + tokens[5].size(), parsedPort);
                if (ec == std::errc{} && parsedPort >= 0 && parsedPort <= 65535) {
                    p.runtime.port = static_cast<uint16_t>(parsedPort);
                }
            }
            if (tokens.size() > 6) p.probe.healthPath = std::string(tokens[6]);
            if (tokens.size() > 7) p.gateway.host = std::string(tokens[7]);

            view.systems.push_back(std::move(p));
        }
    }

    return view;
}

EcosystemView parseProjectionFile(const std::filesystem::path& path) {
    if (path.empty()) return {};
    std::ifstream file(path);
    if (!file) return {};
    std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    return parseProjection(content);
}

HealthObservation observeLoopbackHealth(
    uint16_t port,
    std::string_view path,
    int timeoutMilliseconds) noexcept {
    try {
        if (port == 0) {
            return { "offline", 0, "invalid_port" };
        }
        if (path.empty() || path.front() != '/' ||
            path.find_first_of("\r\n") != std::string_view::npos) {
            return { "not_observed", 0, "invalid_health_path" };
        }

        auto upstream = connectLoopback(port, timeoutMilliseconds);
        const std::string request =
            "GET " + std::string(path) + " HTTP/1.1\r\n"
            "Host: 127.0.0.1:" + std::to_string(port) + "\r\n"
            "Accept: application/json\r\n"
            "Connection: close\r\n\r\n";
        if (!sendAll(upstream.get(), request)) {
            return { "offline", 0, "health_request_send_failed" };
        }

        std::string response;
        response.reserve(4 * 1024);
        std::array<char, 4 * 1024> buffer{};
        while (response.find("\r\n\r\n") == std::string::npos) {
            const auto count = recv(upstream.get(), buffer.data(), buffer.size(), 0);
            if (count == 0) break;
            if (count < 0) {
                if (errno == EINTR) continue;
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    return { "offline", 0, "health_response_timeout" };
                }
                return { "offline", 0, "health_response_read_failed" };
            }
            if (response.size() + static_cast<std::size_t>(count) > 64 * 1024) {
                return { "offline", 0, "health_response_headers_too_large" };
            }
            response.append(buffer.data(), static_cast<std::size_t>(count));
        }

        if (!response.starts_with("HTTP/1.") ||
            response.find("\r\n\r\n") == std::string::npos) {
            return { "offline", 0, "invalid_health_response" };
        }

        const int status = statusFromRawHttpResponse(response);
        return {
            status == 200 ? "online" : "offline",
            status,
            status == 200 ? "ok" : "http_" + std::to_string(status)
        };
    } catch (const std::exception& error) {
        return { "offline", 0, error.what() };
    }
}

void observeEcosystemHealth(EcosystemView& view, int timeoutMilliseconds) noexcept {
    for (auto& system : view.systems) {
        if (system.probe.healthPath.empty()) {
            system.health = { "not_observed", 0, "no_probe_declared" };
            continue;
        }
        if (system.runtime.transport != "tcp") {
            system.health = { "not_observed", 0, "unsupported_probe_transport" };
            continue;
        }
        if (system.runtime.listen != "127.0.0.1" && system.runtime.listen != "localhost" && !system.runtime.listen.empty()) {
            system.health = { "not_observed", 0, "unsupported_probe_host" };
            continue;
        }
        system.health = observeLoopbackHealth(system.runtime.port, system.probe.healthPath, timeoutMilliseconds);
    }
}

std::string serializeEcosystemViewJson(const EcosystemView& view) {
    std::string json = "{\n";
    json += "  \"schema\": \"" + jsonEscape(view.schema) + "\",\n";
    json += "  \"composition_id\": \"" + jsonEscape(view.compositionId) + "\",\n";
    json += "  \"deployment_id\": \"" + jsonEscape(view.deploymentId) + "\",\n";
    json += "  \"deployment_status\": \"" + jsonEscape(view.deploymentStatus) + "\",\n";
    json += "  \"systems\": [";

    for (std::size_t i = 0; i < view.systems.size(); ++i) {
        const auto& s = view.systems[i];
        if (i > 0) json += ",";
        json += "\n    {\n";
        json += "      \"component_id\": \"" + jsonEscape(s.componentId) + "\",\n";
        json += "      \"system_id\": \"" + jsonEscape(s.systemId) + "\",\n";
        json += "      \"runtime\": {\n";
        json += "        \"transport\": \"" + jsonEscape(s.runtime.transport) + "\",\n";
        json += "        \"listen\": \"" + jsonEscape(s.runtime.listen) + "\",\n";
        json += "        \"port\": " + std::to_string(s.runtime.port) + "\n";
        json += "      },\n";
        json += "      \"probe\": {\n";
        json += "        \"health_path\": \"" + jsonEscape(s.probe.healthPath) + "\"\n";
        json += "      },\n";
        json += "      \"gateway\": {\n";
        json += "        \"host\": \"" + jsonEscape(s.gateway.host) + "\"\n";
        json += "      },\n";
        json += "      \"health\": {\n";
        json += "        \"status\": \"" + jsonEscape(s.health.status) + "\",\n";
        json += "        \"http_status\": " + std::to_string(s.health.httpStatus) + ",\n";
        json += "        \"detail\": \"" + jsonEscape(s.health.detail) + "\"\n";
        json += "      }\n";
        json += "    }";
    }

    if (!view.systems.empty()) json += "\n  ";
    json += "]\n}";
    return json;
}

std::string serializeSystemsCompatibilityJson(const EcosystemView& view) {
    std::string json = "[";
    for (std::size_t i = 0; i < view.systems.size(); ++i) {
        const auto& s = view.systems[i];
        if (i > 0) json += ",";
        json += "\n  {\n";
        json += "    \"id\": \"" + jsonEscape(s.systemId.empty() ? s.componentId : s.systemId) + "\",\n";
        json += "    \"component_id\": \"" + jsonEscape(s.componentId) + "\",\n";
        json += "    \"system_id\": \"" + jsonEscape(s.systemId) + "\",\n";
        json += "    \"runtime\": {\n";
        json += "      \"transport\": \"" + jsonEscape(s.runtime.transport) + "\",\n";
        json += "      \"listen\": \"" + jsonEscape(s.runtime.listen) + "\",\n";
        json += "      \"port\": " + std::to_string(s.runtime.port) + "\n";
        json += "    },\n";
        json += "    \"probe\": {\n";
        json += "      \"health_path\": \"" + jsonEscape(s.probe.healthPath) + "\"\n";
        json += "      },\n";
        json += "    \"gateway\": {\n";
        json += "      \"host\": \"" + jsonEscape(s.gateway.host) + "\"\n";
        json += "    },\n";
        json += "    \"health_status\": \"" + jsonEscape(s.health.status) + "\",\n";
        json += "    \"health_observed_by\": \"sisterd\",\n";
        json += "    \"health_http_status\": " + std::to_string(s.health.httpStatus) + ",\n";
        json += "    \"health_detail\": \"" + jsonEscape(s.health.detail) + "\",\n";
        json += "    \"health\": {\n";
        json += "      \"status\": \"" + jsonEscape(s.health.status) + "\",\n";
        json += "      \"http_status\": " + std::to_string(s.health.httpStatus) + ",\n";
        json += "      \"detail\": \"" + jsonEscape(s.health.detail) + "\"\n";
        json += "    }\n";
        json += "  }";
    }
    if (!view.systems.empty()) json += "\n";
    json += "]";
    return json;
}

} // namespace sister::ecosystem
