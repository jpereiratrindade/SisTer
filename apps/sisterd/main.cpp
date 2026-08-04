#include "auth.hpp"
#include "db.hpp"
#include "participation_service.hpp"
#include "api/maturity_routes.hpp"
#include "http/content_length.hpp"
#include "runtime/connection_thread_pool.hpp"
#include "runtime/listener.hpp"
#include "security/login_rate_limiter.hpp"

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#include <openssl/sha.h>

#include <algorithm>
#include <array>
#include <cerrno>
#include <charconv>
#include <chrono>
#include <cctype>
#include <condition_variable>
#include <csignal>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <mutex>
#include <optional>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {

using Clock = std::chrono::steady_clock;

constexpr std::size_t kMaxHeaderBytes = 64 * 1024;
constexpr std::size_t kMaxBodyBytes = 16 * 1024 * 1024;
constexpr std::size_t kMaxProxyResponseBytes = 8 * 1024 * 1024;
constexpr std::size_t kMaxStaticFileBytes = 16 * 1024 * 1024;
constexpr std::size_t kMaxRequestTargetBytes = 8 * 1024;
constexpr std::size_t kMaxHeaderCount = 100;
constexpr std::size_t kMaxHeaderLineBytes = 8 * 1024;
constexpr std::size_t kMaxAuthJsonBytes = 64 * 1024;
constexpr std::size_t kMaxMaturityJsonBytes = 512 * 1024;
constexpr std::string_view kSessionCookie = "sister_session";

volatile std::sig_atomic_t gKeepRunning = 1;
std::mutex gLogMutex;

struct ServerConfig {
    int port = 8000;
    std::filesystem::path webRoot = "web";
    std::filesystem::path canonicalWebRoot;
    std::string bindHost = "127.0.0.1";
    bool activatedUnixListener = false;
    std::filesystem::path activatedSocketPath = "/run/sister/sisterd.sock";
    std::filesystem::path authFile = ".run/auth-users.tsv";
    std::filesystem::path maturityRoot = ".run/maturity";
    std::string databaseUrl;
    bool production = true;
    bool secureCookie = true;
    bool hsts = false;
    bool requireSameOrigin = true;
    bool httpBootstrapEnabled = false;
    bool legacyProxyEnabled = false;
    bool legacyWebSocketProxyEnabled = false;
    std::size_t workerThreads = 4;
    std::size_t queueLimit = 256;
    int clientTimeoutSeconds = 10;
    int upstreamTimeoutMilliseconds = 5'000;
    bool referenceSubsystemEnabled = false;
    uint16_t referencePort = 19001;
    std::string internalProxyToken;
    std::string extraConnectSrc;
};

struct HttpRequest {
    std::string method;
    std::string target;
    std::string path;
    std::string query;
    std::string version;
    std::unordered_map<std::string, std::string> headers;
    std::string body;
};

struct HttpResponse {
    int status = 200;
    std::string reason = "OK";
    std::string body;
    std::string contentType = "text/plain; charset=utf-8";
    std::vector<std::pair<std::string, std::string>> headers;
};

struct ReadRequestResult {
    std::optional<HttpRequest> request;
    int status = 400;
    std::string reason = "Bad Request";
    std::string detail = "Requisição inválida.";
};

struct ApiPayload {
    bool found = false;
    bool fallback = false;
    std::string body;
};

struct AppState {
    sisterd::AuthStore auth;
    sisterd::DbConn db;
    sisterd::ParticipationService participation;
    std::mutex authMutex;
    std::mutex dbMutex;

    AppState(const std::filesystem::path& authFile, const std::string& databaseUrl)
        : auth(authFile), db(databaseUrl), participation(db) {}
};

class UniqueFd {
public:
    explicit UniqueFd(int fd = -1) noexcept : fd_(fd) {}
    ~UniqueFd() { reset(); }

    UniqueFd(const UniqueFd&) = delete;
    UniqueFd& operator=(const UniqueFd&) = delete;

    UniqueFd(UniqueFd&& other) noexcept : fd_(std::exchange(other.fd_, -1)) {}
    UniqueFd& operator=(UniqueFd&& other) noexcept {
        if (this != &other) {
            reset(std::exchange(other.fd_, -1));
        }
        return *this;
    }

    [[nodiscard]] int get() const noexcept { return fd_; }
    [[nodiscard]] explicit operator bool() const noexcept { return fd_ >= 0; }

    int release() noexcept { return std::exchange(fd_, -1); }

    void reset(int fd = -1) noexcept {
        if (fd_ >= 0) close(fd_);
        fd_ = fd;
    }

private:
    int fd_;
};

void handleSignal(int) {
    gKeepRunning = 0;
}

std::string lowercase(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char character) {
        return static_cast<char>(std::tolower(character));
    });
    return value;
}

std::string trim(std::string value) {
    const auto first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return {};
    const auto last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

bool parseBool(std::string_view value, bool fallback) {
    if (value.empty()) return fallback;
    const auto normalized = lowercase(std::string(value));
    if (normalized == "1" || normalized == "true" || normalized == "yes" || normalized == "on") return true;
    if (normalized == "0" || normalized == "false" || normalized == "no" || normalized == "off") return false;
    throw std::runtime_error("invalid boolean configuration value: " + std::string(value));
}

std::optional<std::string> environment(std::string_view name) {
    if (const char* value = std::getenv(std::string(name).c_str()); value != nullptr) {
        return std::string(value);
    }
    return std::nullopt;
}

template <typename Integer>
Integer parseInteger(std::string_view value, Integer minimum, Integer maximum, std::string_view label) {
    Integer result{};
    const char* begin = value.data();
    const char* end = value.data() + value.size();
    const auto [pointer, error] = std::from_chars(begin, end, result);
    if (error != std::errc{} || pointer != end || result < minimum || result > maximum) {
        throw std::runtime_error("invalid " + std::string(label) + ": " + std::string(value));
    }
    return result;
}

bool isIpv4Loopback(std::string_view host) {
    in_addr address{};
    if (inet_pton(AF_INET, std::string(host).c_str(), &address) != 1) return false;
    return (ntohl(address.s_addr) & 0xff000000u) == 0x7f000000u;
}

ServerConfig loadConfig(int argc, char** argv) {
    ServerConfig config;

    const std::string environmentName = lowercase(environment("SISTER_ENV").value_or("production"));
    if (environmentName == "production" || environmentName == "prod") {
        config.production = true;
    } else if (environmentName == "development" || environmentName == "dev" ||
               environmentName == "test") {
        config.production = false;
    } else {
        throw std::runtime_error("invalid SISTER_ENV: " + environmentName);
    }

    const std::string listenerMode = lowercase(environment("SISTER_LISTENER_MODE").value_or(
        config.production ? "systemd-unix" : "tcp-loopback"));
    if (listenerMode == "systemd-unix") {
        config.activatedUnixListener = true;
    } else if (listenerMode == "tcp-loopback") {
        config.activatedUnixListener = false;
    } else {
        throw std::runtime_error("invalid SISTER_LISTENER_MODE: " + listenerMode);
    }
    config.activatedSocketPath = environment("SISTER_ACTIVATED_SOCKET_PATH")
        .value_or("/run/sister/sisterd.sock");

    if (config.production) {
        if (!config.activatedUnixListener) {
            throw std::runtime_error("production sisterd requires the systemd-activated Unix listener");
        }
        if (config.activatedSocketPath != "/run/sister/sisterd.sock") {
            throw std::runtime_error("production sisterd requires /run/sister/sisterd.sock");
        }
        if (environment("SISTER_BIND_HOST") || environment("SISTER_PORT") || argc >= 2) {
            throw std::runtime_error("production TCP listener configuration is forbidden");
        }
    } else if (!config.activatedUnixListener) {
        const auto configuredPort = environment("SISTER_PORT").value_or("8000");
        config.port = parseInteger<int>(configuredPort, 1, 65535, "SISTER_PORT");
        if (argc >= 2) config.port = parseInteger<int>(argv[1], 1, 65535, "port argument");
    } else if (argc >= 2) {
        throw std::runtime_error("port argument cannot be combined with an activated Unix listener");
    }

    config.webRoot = environment("SISTER_WEB_ROOT").value_or("web");
    if (argc >= 3) config.webRoot = argv[2];

    config.bindHost = environment("SISTER_BIND_HOST").value_or("127.0.0.1");
    config.authFile = environment("SISTER_AUTH_FILE").value_or(".run/auth-users.tsv");
    config.maturityRoot = environment("SISTER_MATURITY_ROOT").value_or(".run/maturity");
    config.databaseUrl = environment("SISTER_DATABASE_URL").value_or("");

    config.secureCookie = parseBool(
        environment("SISTER_COOKIE_SECURE").value_or(config.production ? "true" : "false"),
        config.production);
    config.hsts = parseBool(environment("SISTER_HSTS").value_or("false"), false);
    config.requireSameOrigin = parseBool(
        environment("SISTER_REQUIRE_SAME_ORIGIN").value_or(config.production ? "true" : "false"),
        config.production);
    config.httpBootstrapEnabled = parseBool(
        environment("SISTER_ENABLE_HTTP_BOOTSTRAP").value_or(config.production ? "false" : "true"),
        !config.production);
    config.legacyProxyEnabled = parseBool(
        environment("SISTER_ENABLE_LEGACY_PROXY").value_or("false"), false);
    config.legacyWebSocketProxyEnabled = parseBool(
        environment("SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY").value_or("false"), false);

    const auto tcpFallback = environment("SISTER_ALLOW_TCP_FALLBACK");
    if (tcpFallback && parseBool(*tcpFallback, false)) {
        throw std::runtime_error("TCP listener fallback is forbidden");
    }
    if (!config.activatedUnixListener && !isIpv4Loopback(config.bindHost)) {
        throw std::runtime_error("TCP listener requires an IPv4 loopback address");
    }
    if (config.production && config.httpBootstrapEnabled) {
        throw std::runtime_error(
            "HTTP administrator bootstrap is forbidden in production; use sisterctl auth bootstrap-admin");
    }
    if (config.production && config.legacyProxyEnabled) {
        throw std::runtime_error("legacy HTTP proxy is forbidden in production");
    }
    if (config.production && config.legacyWebSocketProxyEnabled) {
        throw std::runtime_error("legacy WebSocket proxy is forbidden in production");
    }
    if (config.legacyWebSocketProxyEnabled && !config.legacyProxyEnabled) {
        throw std::runtime_error(
            "SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY requires SISTER_ENABLE_LEGACY_PROXY");
    }

    const auto hardwareThreads = std::max(2u, std::thread::hardware_concurrency());
    config.workerThreads = parseInteger<std::size_t>(
        environment("SISTER_WORKERS").value_or(std::to_string(std::min(16u, hardwareThreads))),
        1, 64, "SISTER_WORKERS");
    config.queueLimit = parseInteger<std::size_t>(
        environment("SISTER_QUEUE_LIMIT").value_or("256"), 16, 4096, "SISTER_QUEUE_LIMIT");
    config.clientTimeoutSeconds = parseInteger<int>(
        environment("SISTER_CLIENT_TIMEOUT_SECONDS").value_or("10"),
        1, 120, "SISTER_CLIENT_TIMEOUT_SECONDS");
    config.upstreamTimeoutMilliseconds = parseInteger<int>(
        environment("SISTER_UPSTREAM_TIMEOUT_MS").value_or("5000"),
        100, 120'000, "SISTER_UPSTREAM_TIMEOUT_MS");
    config.referenceSubsystemEnabled = parseBool(
        environment("SISTER_ENABLE_REFERENCE_SUBSYSTEM").value_or("false"), false);
    config.referencePort = parseInteger<uint16_t>(
        environment("SISTER_REFERENCE_PORT").value_or("19001"),
        1, std::numeric_limits<uint16_t>::max(), "SISTER_REFERENCE_PORT");
    config.internalProxyToken = environment("SISTER_INTERNAL_PROXY_TOKEN").value_or("");
    config.extraConnectSrc = environment("SISTER_EXTRA_CONNECT_SRC").value_or("");
    if (config.referenceSubsystemEnabled && config.internalProxyToken.size() < 32) {
        throw std::runtime_error(
            "SISTER_ENABLE_REFERENCE_SUBSYSTEM requires SISTER_INTERNAL_PROXY_TOKEN");
    }

    std::error_code error;
    config.canonicalWebRoot = std::filesystem::weakly_canonical(config.webRoot, error);
    if (error || !std::filesystem::is_directory(config.canonicalWebRoot)) {
        throw std::runtime_error("web root is not a readable directory: " + config.webRoot.string());
    }

    return config;
}

std::string logSafe(std::string_view value) {
    std::string result;
    result.reserve(std::min<std::size_t>(value.size(), 512));
    for (const unsigned char character : value) {
        if (result.size() >= 512) break;
        if (character == '\r' || character == '\n' || character == '\t') {
            result.push_back(' ');
        } else if (character >= 0x20 && character != 0x7f) {
            result.push_back(static_cast<char>(character));
        }
    }
    return result;
}

void logUnhandledWorkerException(std::string_view detail) {
    std::lock_guard lock(gLogMutex);
    std::cerr << "level=error event=unhandled_worker_exception detail=\""
              << logSafe(detail) << "\"\n";
}

void logEvent(
    std::string_view level,
    std::string_view requestId,
    std::string_view peer,
    std::string_view method,
    std::string_view path,
    int status,
    std::chrono::milliseconds elapsed,
    std::string_view detail = {}) {
    std::lock_guard lock(gLogMutex);
    std::cerr << "level=" << level
              << " request_id=" << logSafe(requestId)
              << " peer=\"" << logSafe(peer) << '\"'
              << " method=\"" << logSafe(method) << '\"'
              << " path=\"" << logSafe(path) << '\"'
              << " status=" << status
              << " duration_ms=" << elapsed.count();
    if (!detail.empty()) std::cerr << " detail=\"" << logSafe(detail) << '\"';
    std::cerr << '\n';
}

std::string randomHex(std::size_t bytes) {
    thread_local std::mt19937_64 generator([] {
        std::array<std::uint32_t, 8> seedData{};
        std::random_device device;
        for (auto& value : seedData) value = device();
        std::seed_seq sequence(seedData.begin(), seedData.end());
        return std::mt19937_64(sequence);
    }());

    static constexpr char digits[] = "0123456789abcdef";
    std::string result;
    result.resize(bytes * 2);
    for (std::size_t i = 0; i < bytes; ++i) {
        const auto value = static_cast<unsigned char>(generator() & 0xffu);
        result[i * 2] = digits[value >> 4u];
        result[i * 2 + 1] = digits[value & 0x0fu];
    }
    return result;
}

std::string sha256Hex(std::string_view value) {
    std::array<unsigned char, SHA256_DIGEST_LENGTH> digest{};
    SHA256(
        reinterpret_cast<const unsigned char*>(value.data()),
        value.size(),
        digest.data());
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (const auto byte : digest) {
        out << std::setw(2) << static_cast<int>(byte);
    }
    return out.str();
}

std::string rawHttpBody(std::string_view response) {
    const auto separator = response.find("\r\n\r\n");
    if (separator == std::string_view::npos) return {};
    return std::string(response.substr(separator + 4));
}

bool isTokenCharacter(unsigned char character) {
    if (std::isalnum(character)) return true;
    constexpr std::string_view extras = "!#$%&'*+-.^_`|~";
    return extras.find(static_cast<char>(character)) != std::string_view::npos;
}

bool containsInvalidHeaderValueCharacter(std::string_view value) {
    return std::any_of(value.begin(), value.end(), [](unsigned char character) {
        return (character < 0x20 && character != '\t') || character == 0x7f;
    });
}

bool isValidHeaderName(std::string_view name) {
    return !name.empty() && std::all_of(name.begin(), name.end(), [](unsigned char character) {
        return isTokenCharacter(character);
    });
}

std::optional<std::string> percentDecodePath(std::string_view encoded) {
    auto hexValue = [](char character) -> int {
        if (character >= '0' && character <= '9') return character - '0';
        if (character >= 'a' && character <= 'f') return character - 'a' + 10;
        if (character >= 'A' && character <= 'F') return character - 'A' + 10;
        return -1;
    };

    std::string decoded;
    decoded.reserve(encoded.size());
    for (std::size_t index = 0; index < encoded.size(); ++index) {
        unsigned char value = static_cast<unsigned char>(encoded[index]);
        if (encoded[index] == '%') {
            if (index + 2 >= encoded.size()) return std::nullopt;
            const int high = hexValue(encoded[index + 1]);
            const int low = hexValue(encoded[index + 2]);
            if (high < 0 || low < 0) return std::nullopt;
            value = static_cast<unsigned char>((high << 4) | low);
            index += 2;
        }
        if (value == 0 || value == '\\' || value < 0x20 || value == 0x7f) return std::nullopt;
        decoded.push_back(static_cast<char>(value));
    }
    return decoded;
}

ReadRequestResult readRequest(int client) {
    ReadRequestResult failure;
    std::string raw;
    raw.reserve(8 * 1024);

    std::size_t headerEnd = std::string::npos;
    while (headerEnd == std::string::npos) {
        char buffer[8192];
        const auto received = recv(client, buffer, sizeof(buffer), 0);
        if (received == 0) {
            failure.detail = "Conexão encerrada antes do cabeçalho HTTP completo.";
            return failure;
        }
        if (received < 0) {
            if (errno == EINTR) continue;
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                failure.status = 408;
                failure.reason = "Request Timeout";
                failure.detail = "Tempo excedido ao receber a requisição.";
            }
            return failure;
        }
        raw.append(buffer, static_cast<std::size_t>(received));
        headerEnd = raw.find("\r\n\r\n");
        if (headerEnd == std::string::npos && raw.size() > kMaxHeaderBytes) {
            failure.status = 431;
            failure.reason = "Request Header Fields Too Large";
            failure.detail = "Cabeçalhos HTTP excedem o limite permitido.";
            return failure;
        }
        if (headerEnd != std::string::npos && headerEnd > kMaxHeaderBytes) {
            failure.status = 431;
            failure.reason = "Request Header Fields Too Large";
            failure.detail = "Cabeçalhos HTTP excedem o limite permitido.";
            return failure;
        }
    }

    HttpRequest request;
    std::istringstream headerStream(raw.substr(0, headerEnd));
    std::string line;
    if (!std::getline(headerStream, line)) return failure;
    if (!line.empty() && line.back() == '\r') line.pop_back();

    {
        std::istringstream startLine(line);
        std::string extra;
        if (!(startLine >> request.method >> request.target >> request.version) || (startLine >> extra)) {
            failure.detail = "Linha inicial HTTP inválida.";
            return failure;
        }
    }

    if (request.method.empty() || request.method.size() > 16 ||
        !std::all_of(request.method.begin(), request.method.end(), [](unsigned char character) {
            return isTokenCharacter(character);
        })) {
        failure.detail = "Método HTTP inválido.";
        return failure;
    }

    if (request.version != "HTTP/1.1" && request.version != "HTTP/1.0") {
        failure.status = 505;
        failure.reason = "HTTP Version Not Supported";
        failure.detail = "Apenas HTTP/1.0 e HTTP/1.1 são aceitos.";
        return failure;
    }

    if (request.target.empty() || request.target.size() > kMaxRequestTargetBytes || request.target.front() != '/' ||
        request.target.find('#') != std::string::npos || containsInvalidHeaderValueCharacter(request.target)) {
        failure.status = 414;
        failure.reason = "URI Too Long";
        failure.detail = "Alvo da requisição inválido.";
        return failure;
    }

    std::size_t headerCount = 0;
    while (std::getline(headerStream, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        if (++headerCount > kMaxHeaderCount || line.size() > kMaxHeaderLineBytes) {
            failure.status = 431;
            failure.reason = "Request Header Fields Too Large";
            failure.detail = "Quantidade ou tamanho dos cabeçalhos excede o limite.";
            return failure;
        }
        if (line.front() == ' ' || line.front() == '\t') {
            failure.detail = "Continuação obsoleta de cabeçalho não é aceita.";
            return failure;
        }
        const auto separator = line.find(':');
        if (separator == std::string::npos) {
            failure.detail = "Cabeçalho HTTP malformado.";
            return failure;
        }
        std::string name = lowercase(trim(line.substr(0, separator)));
        std::string value = trim(line.substr(separator + 1));
        if (!isValidHeaderName(name) || containsInvalidHeaderValueCharacter(value)) {
            failure.detail = "Nome ou valor de cabeçalho inválido.";
            return failure;
        }

        const auto existing = request.headers.find(name);
        if (existing != request.headers.end()) {
            if (name == "cookie") {
                existing->second += "; " + value;
                continue;
            }
            failure.detail = "Cabeçalhos duplicados não são aceitos.";
            return failure;
        }
        request.headers.emplace(std::move(name), std::move(value));
    }

    if (request.version == "HTTP/1.1" && !request.headers.contains("host")) {
        failure.detail = "Cabeçalho Host obrigatório em HTTP/1.1.";
        return failure;
    }

    if (request.headers.contains("transfer-encoding")) {
        failure.status = 501;
        failure.reason = "Not Implemented";
        failure.detail = "Transfer-Encoding não é aceito neste servidor.";
        return failure;
    }

    if (const auto expect = request.headers.find("expect"); expect != request.headers.end()) {
        failure.status = 417;
        failure.reason = "Expectation Failed";
        failure.detail = "Expect não é suportado.";
        return failure;
    }

    std::size_t contentLength = 0;
    if (const auto length = request.headers.find("content-length"); length != request.headers.end()) {
        const auto parsed = sisterd::http::parseContentLength(length->second, kMaxBodyBytes);
        if (parsed.status == sisterd::http::ContentLengthStatus::invalid) {
            failure.status = 400;
            failure.reason = "Bad Request";
            failure.detail = "Content-Length inválido.";
            return failure;
        }
        if (parsed.status == sisterd::http::ContentLengthStatus::tooLarge) {
            failure.status = 413;
            failure.reason = "Payload Too Large";
            failure.detail = "Corpo HTTP excede o limite permitido.";
            return failure;
        }
        contentLength = parsed.value;
    }

    const std::size_t expectedSize = headerEnd + 4 + contentLength;
    while (raw.size() < expectedSize) {
        char buffer[8192];
        const auto received = recv(client, buffer, sizeof(buffer), 0);
        if (received == 0) {
            failure.detail = "Corpo HTTP encerrado antes do tamanho declarado.";
            return failure;
        }
        if (received < 0) {
            if (errno == EINTR) continue;
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                failure.status = 408;
                failure.reason = "Request Timeout";
                failure.detail = "Tempo excedido ao receber o corpo da requisição.";
            }
            return failure;
        }
        raw.append(buffer, static_cast<std::size_t>(received));
        if (raw.size() > expectedSize + 8192) {
            failure.detail = "Dados excedentes inesperados após o corpo HTTP.";
            return failure;
        }
    }

    request.body = raw.substr(headerEnd + 4, contentLength);

    const auto queryPosition = request.target.find('?');
    const std::string_view encodedPath = queryPosition == std::string::npos
        ? std::string_view(request.target)
        : std::string_view(request.target).substr(0, queryPosition);
    if (queryPosition != std::string::npos) request.query = request.target.substr(queryPosition);

    const auto decodedPath = percentDecodePath(encodedPath);
    if (!decodedPath || decodedPath->empty() || decodedPath->front() != '/') {
        failure.detail = "Caminho de URL inválido.";
        return failure;
    }
    request.path = *decodedPath;

    return {std::move(request), 200, "OK", {}};
}

std::string jsonEscape(std::string_view value) {
    std::string escaped;
    escaped.reserve(value.size());
    for (const unsigned char character : value) {
        switch (character) {
            case '\\': escaped += "\\\\"; break;
            case '"': escaped += "\\\""; break;
            case '\b': escaped += "\\b"; break;
            case '\f': escaped += "\\f"; break;
            case '\n': escaped += "\\n"; break;
            case '\r': escaped += "\\r"; break;
            case '\t': escaped += "\\t"; break;
            default:
                if (character < 0x20) {
                    std::ostringstream code;
                    code << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                         << static_cast<unsigned int>(character);
                    escaped += code.str();
                } else {
                    escaped.push_back(static_cast<char>(character));
                }
        }
    }
    return escaped;
}

void appendUtf8(std::string& output, std::uint32_t codePoint) {
    if (codePoint <= 0x7f) {
        output.push_back(static_cast<char>(codePoint));
    } else if (codePoint <= 0x7ff) {
        output.push_back(static_cast<char>(0xc0 | (codePoint >> 6)));
        output.push_back(static_cast<char>(0x80 | (codePoint & 0x3f)));
    } else if (codePoint <= 0xffff) {
        output.push_back(static_cast<char>(0xe0 | (codePoint >> 12)));
        output.push_back(static_cast<char>(0x80 | ((codePoint >> 6) & 0x3f)));
        output.push_back(static_cast<char>(0x80 | (codePoint & 0x3f)));
    } else if (codePoint <= 0x10ffff) {
        output.push_back(static_cast<char>(0xf0 | (codePoint >> 18)));
        output.push_back(static_cast<char>(0x80 | ((codePoint >> 12) & 0x3f)));
        output.push_back(static_cast<char>(0x80 | ((codePoint >> 6) & 0x3f)));
        output.push_back(static_cast<char>(0x80 | (codePoint & 0x3f)));
    } else {
        throw std::runtime_error("invalid Unicode code point");
    }
}

class FlatJsonObjectParser {
public:
    explicit FlatJsonObjectParser(std::string_view input) : input_(input) {}

    std::optional<std::unordered_map<std::string, std::optional<std::string>>> parse() {
        try {
            skipWhitespace();
            expect('{');
            skipWhitespace();

            std::unordered_map<std::string, std::optional<std::string>> result;
            if (consume('}')) {
                skipWhitespace();
                if (position_ != input_.size()) return std::nullopt;
                return result;
            }

            for (;;) {
                skipWhitespace();
                const std::string key = parseString();
                if (result.contains(key)) return std::nullopt;
                skipWhitespace();
                expect(':');
                skipWhitespace();

                std::optional<std::string> value;
                if (peek() == '"') {
                    value = parseString();
                } else if (input_.substr(position_, 4) == "null") {
                    position_ += 4;
                } else {
                    return std::nullopt;
                }
                result.emplace(key, std::move(value));

                skipWhitespace();
                if (consume('}')) break;
                expect(',');
            }

            skipWhitespace();
            if (position_ != input_.size()) return std::nullopt;
            return result;
        } catch (const std::exception&) {
            return std::nullopt;
        }
    }

private:
    char peek() const {
        if (position_ >= input_.size()) throw std::runtime_error("unexpected end of JSON");
        return input_[position_];
    }

    bool consume(char expected) {
        if (position_ < input_.size() && input_[position_] == expected) {
            ++position_;
            return true;
        }
        return false;
    }

    void expect(char expected) {
        if (!consume(expected)) throw std::runtime_error("unexpected JSON token");
    }

    void skipWhitespace() {
        while (position_ < input_.size() &&
               (input_[position_] == ' ' || input_[position_] == '\t' ||
                input_[position_] == '\r' || input_[position_] == '\n')) {
            ++position_;
        }
    }

    std::uint32_t parseHex4() {
        if (position_ + 4 > input_.size()) throw std::runtime_error("incomplete Unicode escape");
        std::uint32_t result = 0;
        for (int i = 0; i < 4; ++i) {
            const char character = input_[position_++];
            result <<= 4;
            if (character >= '0' && character <= '9') result |= character - '0';
            else if (character >= 'a' && character <= 'f') result |= character - 'a' + 10;
            else if (character >= 'A' && character <= 'F') result |= character - 'A' + 10;
            else throw std::runtime_error("invalid Unicode escape");
        }
        return result;
    }

    std::string parseString() {
        expect('"');
        std::string result;
        while (position_ < input_.size()) {
            const unsigned char character = static_cast<unsigned char>(input_[position_++]);
            if (character == '"') return result;
            if (character < 0x20) throw std::runtime_error("control character in JSON string");
            if (character != '\\') {
                result.push_back(static_cast<char>(character));
                continue;
            }

            if (position_ >= input_.size()) throw std::runtime_error("incomplete JSON escape");
            const char escape = input_[position_++];
            switch (escape) {
                case '"': result.push_back('"'); break;
                case '\\': result.push_back('\\'); break;
                case '/': result.push_back('/'); break;
                case 'b': result.push_back('\b'); break;
                case 'f': result.push_back('\f'); break;
                case 'n': result.push_back('\n'); break;
                case 'r': result.push_back('\r'); break;
                case 't': result.push_back('\t'); break;
                case 'u': {
                    std::uint32_t codePoint = parseHex4();
                    if (codePoint >= 0xd800 && codePoint <= 0xdbff) {
                        if (position_ + 2 > input_.size() || input_[position_] != '\\' || input_[position_ + 1] != 'u') {
                            throw std::runtime_error("missing low surrogate");
                        }
                        position_ += 2;
                        const std::uint32_t low = parseHex4();
                        if (low < 0xdc00 || low > 0xdfff) throw std::runtime_error("invalid low surrogate");
                        codePoint = 0x10000 + ((codePoint - 0xd800) << 10) + (low - 0xdc00);
                    } else if (codePoint >= 0xdc00 && codePoint <= 0xdfff) {
                        throw std::runtime_error("orphan low surrogate");
                    }
                    appendUtf8(result, codePoint);
                    break;
                }
                default: throw std::runtime_error("invalid JSON escape");
            }
        }
        throw std::runtime_error("unterminated JSON string");
    }

    std::string_view input_;
    std::size_t position_ = 0;
};

std::optional<std::unordered_map<std::string, std::optional<std::string>>> parseFlatJsonObject(
    std::string_view body) {
    if (body.size() > kMaxAuthJsonBytes) return std::nullopt;
    return FlatJsonObjectParser(body).parse();
}

std::optional<std::string> jsonStringField(
    const std::unordered_map<std::string, std::optional<std::string>>& object,
    std::string_view key) {
    const auto found = object.find(std::string(key));
    if (found == object.end() || !found->second) return std::nullopt;
    return *found->second;
}

std::string cookieValue(const HttpRequest& request, std::string_view name) {
    const auto found = request.headers.find("cookie");
    if (found == request.headers.end()) return {};

    std::istringstream cookies(found->second);
    std::string item;
    while (std::getline(cookies, item, ';')) {
        item = trim(item);
        const auto separator = item.find('=');
        if (separator != std::string::npos && item.substr(0, separator) == name) {
            return item.substr(separator + 1);
        }
    }
    return {};
}

std::string sessionCookieAttributes(const ServerConfig& config) {
    return std::string("; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800") +
        (config.secureCookie ? "; Secure" : "");
}

std::vector<std::pair<std::string, std::string>> sessionHeaders(
    const std::string& token,
    const ServerConfig& config) {
    return {
        {"Set-Cookie", std::string(kSessionCookie) + "=" + token + sessionCookieAttributes(config)},
        {"Cache-Control", "no-store"}
    };
}

std::vector<std::pair<std::string, std::string>> clearSessionHeaders(const ServerConfig& config) {
    return {
        {"Set-Cookie", std::string(kSessionCookie) +
            "=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0" +
            (config.secureCookie ? "; Secure" : "")},
        {"Cache-Control", "no-store"}
    };
}

bool isUnsafeMethod(std::string_view method) {
    return method != "GET" && method != "HEAD" && method != "OPTIONS";
}

std::optional<std::string> authorityFromUrl(std::string_view url) {
    const auto scheme = url.find("://");
    if (scheme == std::string_view::npos) return std::nullopt;
    const auto authorityStart = scheme + 3;
    const auto authorityEnd = url.find_first_of("/?#", authorityStart);
    std::string authority(url.substr(
        authorityStart,
        authorityEnd == std::string_view::npos ? std::string_view::npos : authorityEnd - authorityStart));
    if (authority.empty() || authority.find('@') != std::string::npos || authority.find(',') != std::string::npos) {
        return std::nullopt;
    }
    return lowercase(trim(authority));
}

bool sameOriginRequest(const HttpRequest& request, const ServerConfig& config) {
    if (!isUnsafeMethod(request.method)) return true;

    const auto hostIterator = request.headers.find("host");
    if (hostIterator == request.headers.end()) return !config.requireSameOrigin;
    const std::string host = lowercase(trim(hostIterator->second));
    if (host.empty() || host.find(',') != std::string::npos) return false;

    if (const auto origin = request.headers.find("origin"); origin != request.headers.end()) {
        if (origin->second == "null") return false;
        const auto authority = authorityFromUrl(origin->second);
        return authority && *authority == host;
    }

    if (const auto referer = request.headers.find("referer"); referer != request.headers.end()) {
        const auto authority = authorityFromUrl(referer->second);
        return authority && *authority == host;
    }

    if (const auto fetchSite = request.headers.find("sec-fetch-site"); fetchSite != request.headers.end()) {
        const auto value = lowercase(trim(fetchSite->second));
        return value == "same-origin" || value == "none";
    }

    return !config.requireSameOrigin;
}

std::string contentType(const std::filesystem::path& path) {
    const auto extension = lowercase(path.extension().string());
    if (extension == ".html") return "text/html; charset=utf-8";
    if (extension == ".css") return "text/css; charset=utf-8";
    if (extension == ".js" || extension == ".mjs") return "application/javascript; charset=utf-8";
    if (extension == ".json") return "application/json; charset=utf-8";
    if (extension == ".svg") return "image/svg+xml";
    if (extension == ".png") return "image/png";
    if (extension == ".jpg" || extension == ".jpeg") return "image/jpeg";
    if (extension == ".webp") return "image/webp";
    if (extension == ".ico") return "image/x-icon";
    if (extension == ".woff2") return "font/woff2";
    return "application/octet-stream";
}

bool shouldNeverCacheStaticFile(const std::filesystem::path& path) {
    const auto extension = lowercase(path.extension().string());
    return extension == ".html" || extension == ".css" || extension == ".js" ||
           extension == ".mjs" || extension == ".json";
}

bool shouldClearBrowserSiteData(const std::filesystem::path& path) {
    const auto extension = lowercase(path.extension().string());
    return extension == ".html" || extension == ".js" || extension == ".mjs";
}

std::string readFile(const std::filesystem::path& path) {
    std::error_code error;
    const auto size = std::filesystem::file_size(path, error);
    if (error || size > kMaxStaticFileBytes) throw std::runtime_error("static file unavailable or too large");

    std::ifstream input(path, std::ios::binary);
    if (!input) throw std::runtime_error("static file not found");
    std::string body(static_cast<std::size_t>(size), '\0');
    if (size > 0 && !input.read(body.data(), static_cast<std::streamsize>(size))) {
        throw std::runtime_error("cannot read static file");
    }
    return body;
}

enum class FixedJsonState { Ready, Missing, Invalid };

struct FixedJsonDocument {
    FixedJsonState state = FixedJsonState::Missing;
    std::string body;
};

bool hasJsonStringField(std::string_view document, std::string_view name, std::string_view value) {
    const std::string key = "\"" + std::string(name) + "\"";
    auto position = document.find(key);
    if (position == std::string_view::npos) return false;
    position = document.find(':', position + key.size());
    if (position == std::string_view::npos) return false;
    ++position;
    while (position < document.size() && std::isspace(static_cast<unsigned char>(document[position]))) {
        ++position;
    }
    const std::string expected = "\"" + std::string(value) + "\"";
    return document.substr(position, expected.size()) == expected;
}

FixedJsonDocument readFixedJsonDocument(
    const std::filesystem::path& path,
    std::string_view expectedSchema) {
    std::error_code error;
    const auto status = std::filesystem::symlink_status(path, error);
    if (error) {
        if (error == std::errc::no_such_file_or_directory ||
            error == std::errc::not_a_directory) {
            return {FixedJsonState::Missing, {}};
        }
        return {FixedJsonState::Invalid, {}};
    }
    if (!std::filesystem::exists(status)) return {FixedJsonState::Missing, {}};
    if (!std::filesystem::is_regular_file(status)) return {FixedJsonState::Invalid, {}};
    const auto size = std::filesystem::file_size(path, error);
    if (error || size == 0 || size > kMaxMaturityJsonBytes) {
        return {FixedJsonState::Invalid, {}};
    }

    std::ifstream input(path, std::ios::binary);
    if (!input) return {FixedJsonState::Invalid, {}};
    std::string body(static_cast<std::size_t>(size), '\0');
    if (!input.read(body.data(), static_cast<std::streamsize>(size))) {
        return {FixedJsonState::Invalid, {}};
    }

    const auto first = body.find_first_not_of(" \t\r\n");
    const auto last = body.find_last_not_of(" \t\r\n");
    if (first == std::string::npos || body[first] != '{' || body[last] != '}' ||
        !hasJsonStringField(body, "schema", expectedSchema)) {
        return {FixedJsonState::Invalid, {}};
    }
    return {FixedJsonState::Ready, std::move(body)};
}

bool pathStartsWith(const std::filesystem::path& candidate, const std::filesystem::path& root) {
    auto candidateIterator = candidate.begin();
    auto rootIterator = root.begin();
    for (; rootIterator != root.end(); ++rootIterator, ++candidateIterator) {
        if (candidateIterator == candidate.end() || *candidateIterator != *rootIterator) return false;
    }
    return true;
}

std::optional<std::filesystem::path> resolveStaticPath(
    const std::string& rawPath,
    const ServerConfig& config) {
    std::string routePath = rawPath;
    if (routePath.empty() || routePath == "/") routePath = "/index.html";
    else if (routePath == "/login") routePath = "/login.html";
    else if (routePath == "/admin/users") routePath = "/admin.html";
    else if (routePath == "/admin/maturity") routePath = "/maturity/index.html";
    else if (routePath == "/engineering" || routePath == "/engineering/") routePath = "/engineering/index.html";

    std::filesystem::path relative = routePath.substr(1);
    if (relative.empty() || relative.is_absolute()) return std::nullopt;

    for (const auto& component : relative) {
        const auto value = component.string();
        if (value.empty() || value == "." || value == ".." ||
            (value.starts_with('.') && value != ".well-known")) {
            return std::nullopt;
        }
    }

    std::error_code error;
    const auto candidate = std::filesystem::weakly_canonical(config.canonicalWebRoot / relative, error);
    if (error || !pathStartsWith(candidate, config.canonicalWebRoot) ||
        !std::filesystem::is_regular_file(candidate, error)) {
        return std::nullopt;
    }
    return candidate;
}

std::string jsonUser(const sisterd::AuthUser& user) {
    return "{\"id\":\"" + jsonEscape(user.id) +
        "\",\"name\":\"" + jsonEscape(user.name) +
        "\",\"email\":\"" + jsonEscape(user.email) +
        "\",\"role\":\"" + jsonEscape(user.role) + "\"}";
}

std::vector<std::string> capabilitiesForRole(const std::string& role) {
    if (role == "admin") {
        return {
            "session.self.read",
            "engineering.plan.read",
            "engineering.operational-base.read",
            "engineering.integration.decide",
            "engineering.integration.execute",
            "participation.propose",
            "participation.read",
            "identity.users.manage",
            "maturity.evidence.read",
            "subsystem.manifest.read",
            "sister.governance.read",
            "sister.evidence.read",
            "sister.diagnostics.read",
            "reference.identity.read",
            "reference.echo.execute"
        };
    }
    if (role == "researcher" || role == "project_lead") {
        return {
            "session.self.read",
            "subsystem.manifest.read",
            "reference.identity.read",
            "reference.echo.execute"
        };
    }
    if (role == "user" || role == "registered_user" || role == "guest") {
        return {"session.self.read"};
    }
    return {}; // Unknown roles fail closed.
}

bool hasCapability(const sisterd::AuthUser& actor, std::string_view capability) {
    const auto capabilities = capabilitiesForRole(actor.role);
    return std::find(capabilities.begin(), capabilities.end(), capability) != capabilities.end();
}

std::string jsonCapabilities(const sisterd::AuthUser& user) {
    const auto capabilities = capabilitiesForRole(user.role);
    std::string body = "{\"user_id\":\"" + jsonEscape(user.id) +
        "\",\"role\":\"" + jsonEscape(user.role) + "\",\"capabilities\":[";
    for (std::size_t index = 0; index < capabilities.size(); ++index) {
        if (index > 0) body += ',';
        body += "\"" + jsonEscape(capabilities[index]) + "\"";
    }
    body += "]}";
    return body;
}

HttpResponse jsonError(int status, std::string reason, std::string_view detail) {
    return {
        status,
        std::move(reason),
        "{\"detail\":\"" + jsonEscape(detail) + "\"}",
        "application/json; charset=utf-8",
        {{"Cache-Control", "no-store"}}
    };
}

HttpResponse redirectResponse(int status, std::string reason, std::string location) {
    return {
        status,
        std::move(reason),
        {},
        "text/plain; charset=utf-8",
        {{"Location", std::move(location)}, {"Cache-Control", "no-store"}}
    };
}

bool safeResponseHeader(std::string_view name, std::string_view value) {
    return isValidHeaderName(name) && !containsInvalidHeaderValueCharacter(value) &&
           name.find('\r') == std::string_view::npos && name.find('\n') == std::string_view::npos;
}

std::string serializeResponse(
    const HttpResponse& response,
    const ServerConfig& config,
    std::string_view requestId,
    bool headOnly) {
    std::ostringstream output;
    if (containsInvalidHeaderValueCharacter(config.extraConnectSrc)) {
        throw std::runtime_error("unsafe SISTER_EXTRA_CONNECT_SRC");
    }
    output << "HTTP/1.1 " << response.status << ' ' << response.reason << "\r\n";
    if (!response.contentType.empty()) output << "Content-Type: " << response.contentType << "\r\n";
    output << "Content-Length: " << response.body.size() << "\r\n"
           << "Connection: close\r\n"
           << "X-Content-Type-Options: nosniff\r\n"
           << "Referrer-Policy: same-origin\r\n"
           << "X-Frame-Options: DENY\r\n"
           << "Permissions-Policy: geolocation=(), microphone=(), camera=()\r\n"
           << "Cross-Origin-Opener-Policy: same-origin\r\n"
           << "Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; "
              "img-src 'self' data:; connect-src 'self'"
           << (config.extraConnectSrc.empty() ? "" : " " + config.extraConnectSrc)
           << "; font-src 'self'; object-src 'none'; "
              "base-uri 'self'; frame-ancestors 'none'; form-action 'self'\r\n"
           << "X-Request-ID: " << requestId << "\r\n";
    if (config.hsts) output << "Strict-Transport-Security: max-age=31536000; includeSubDomains\r\n";

    for (const auto& [name, value] : response.headers) {
        if (!safeResponseHeader(name, value)) throw std::runtime_error("unsafe response header");
        output << name << ": " << value << "\r\n";
    }
    output << "\r\n";
    if (!headOnly) output << response.body;
    return output.str();
}

ssize_t sendNoSignal(int socket, const void* data, std::size_t size) {
#ifdef MSG_NOSIGNAL
    return send(socket, data, size, MSG_NOSIGNAL);
#else
    return send(socket, data, size, 0);
#endif
}

bool sendAll(int socket, std::string_view data) {
    std::size_t sent = 0;
    while (sent < data.size()) {
        const auto count = sendNoSignal(socket, data.data() + sent, data.size() - sent);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) return false;
        sent += static_cast<std::size_t>(count);
    }
    return true;
}

std::string safeProxyHeaderValue(std::string_view value, std::size_t maximum = 1024) {
    if (value.size() > maximum || containsInvalidHeaderValueCharacter(value) ||
        value.find('\r') != std::string_view::npos || value.find('\n') != std::string_view::npos) {
        throw std::runtime_error("unsafe identity value for subsystem proxy");
    }
    return std::string(value);
}

void setSocketTimeouts(int socket, int timeoutSeconds) {
    timeval timeout{};
    timeout.tv_sec = timeoutSeconds;
    if (setsockopt(socket, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0 ||
        setsockopt(socket, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout)) < 0) {
        throw std::runtime_error("cannot configure socket timeouts");
    }
}

UniqueFd connectLoopback(uint16_t port, int timeoutMilliseconds) {
    UniqueFd upstream(socket(AF_INET, SOCK_STREAM, 0));
    if (!upstream) throw std::runtime_error("cannot create subsystem proxy socket");

    const int originalFlags = fcntl(upstream.get(), F_GETFL, 0);
    if (originalFlags < 0 || fcntl(upstream.get(), F_SETFL, originalFlags | O_NONBLOCK) < 0) {
        throw std::runtime_error("cannot configure nonblocking upstream socket");
    }

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    if (inet_pton(AF_INET, "127.0.0.1", &address.sin_addr) != 1) {
        throw std::runtime_error("cannot configure loopback address");
    }

    const int result = connect(
        upstream.get(), reinterpret_cast<sockaddr*>(&address), sizeof(address));
    if (result < 0 && errno != EINPROGRESS) throw std::runtime_error("subsystem is unavailable");

    if (result < 0) {
        pollfd descriptor{upstream.get(), POLLOUT, 0};
        int ready;
        do {
            ready = poll(&descriptor, 1, timeoutMilliseconds);
        } while (ready < 0 && errno == EINTR);
        if (ready <= 0) throw std::runtime_error("subsystem connection timeout");

        int socketError = 0;
        socklen_t socketErrorSize = sizeof(socketError);
        if (getsockopt(upstream.get(), SOL_SOCKET, SO_ERROR, &socketError, &socketErrorSize) < 0 ||
            socketError != 0) {
            throw std::runtime_error("subsystem connection failed");
        }
    }

    if (fcntl(upstream.get(), F_SETFL, originalFlags) < 0) {
        throw std::runtime_error("cannot restore upstream socket mode");
    }

    const int timeoutSeconds = std::max(1, (timeoutMilliseconds + 999) / 1000);
    setSocketTimeouts(upstream.get(), timeoutSeconds);
    return upstream;
}

std::string proxyToSubsystem(
    const HttpRequest& request,
    const sisterd::AuthUser& actor,
    std::string_view prefix,
    uint16_t port,
    std::string_view serviceName,
    std::string_view requestId,
    const ServerConfig& config) {
    if (!request.path.starts_with(prefix)) throw std::runtime_error("invalid proxy prefix");

    std::string upstreamPath = request.path.substr(prefix.size());
    if (upstreamPath.empty()) upstreamPath = "/";
    upstreamPath += request.query;
    if (upstreamPath.find('\r') != std::string::npos || upstreamPath.find('\n') != std::string::npos) {
        throw std::runtime_error("invalid upstream path");
    }

    auto upstream = connectLoopback(port, config.upstreamTimeoutMilliseconds);

    std::ostringstream forwarded;
    forwarded << request.method << ' ' << upstreamPath << " HTTP/1.1\r\n"
              << "Host: 127.0.0.1:" << port << "\r\n"
              << "X-Sister-Subject: " << safeProxyHeaderValue(actor.id) << "\r\n"
              << "X-Sister-Name: " << safeProxyHeaderValue(actor.name) << "\r\n"
              << "X-Sister-Email: " << safeProxyHeaderValue(actor.email) << "\r\n"
              << "X-Sister-Role: " << safeProxyHeaderValue(actor.role) << "\r\n"
              << "X-Request-ID: " << safeProxyHeaderValue(requestId, 128) << "\r\n";
    if (!config.internalProxyToken.empty()) {
        forwarded << "X-Sister-Proxy-Token: "
                  << safeProxyHeaderValue(config.internalProxyToken, 4096) << "\r\n";
    }

    if (const auto type = request.headers.find("content-type"); type != request.headers.end()) {
        forwarded << "Content-Type: " << safeProxyHeaderValue(type->second) << "\r\n";
    }
    if (const auto accept = request.headers.find("accept"); accept != request.headers.end()) {
        forwarded << "Accept: " << safeProxyHeaderValue(accept->second) << "\r\n";
    }
    if (!request.body.empty()) forwarded << "Content-Length: " << request.body.size() << "\r\n";
    forwarded << "Connection: close\r\n\r\n" << request.body;

    const auto outbound = forwarded.str();
    if (!sendAll(upstream.get(), outbound)) {
        throw std::runtime_error("cannot send request to " + std::string(serviceName));
    }

    std::string response;
    response.reserve(16 * 1024);
    char buffer[16 * 1024];
    for (;;) {
        const auto count = recv(upstream.get(), buffer, sizeof(buffer), 0);
        if (count == 0) break;
        if (count < 0) {
            if (errno == EINTR) continue;
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                throw std::runtime_error(std::string(serviceName) + " response timeout");
            }
            throw std::runtime_error("cannot read response from " + std::string(serviceName));
        }
        if (response.size() + static_cast<std::size_t>(count) > kMaxProxyResponseBytes) {
            throw std::runtime_error(std::string(serviceName) + " response exceeds limit");
        }
        response.append(buffer, static_cast<std::size_t>(count));
    }

    if (response.empty() || !response.starts_with("HTTP/1.")) {
        throw std::runtime_error("invalid response from " + std::string(serviceName));
    }
    if (response.find("\r\n\r\n") == std::string::npos) {
        throw std::runtime_error("incomplete response from " + std::string(serviceName));
    }
    return response;
}

int statusFromRawHttpResponse(std::string_view response) {
    const auto firstSpace = response.find(' ');
    if (firstSpace == std::string_view::npos || firstSpace + 4 > response.size()) return 502;
    int status = 502;
    const auto [pointer, error] = std::from_chars(
        response.data() + firstSpace + 1,
        response.data() + std::min(response.size(), firstSpace + 4),
        status);
    if (error != std::errc{} || pointer != response.data() + firstSpace + 4) return 502;
    return status;
}

constexpr std::string_view kFallbackContracts = R"([
  {"name":"Subsystem Manifest","version":"1.0.0","required":"Sim"},
  {"name":"Reference Subsystem","version":"0.1.0","required":"Para validacao funcional, operacional e de seguranca"},
  {"name":"Evidence","version":"0.1.0","required":"Para resultado promovido"}
])";

constexpr std::string_view kFallbackSystems = R"([
  {"id":"sister_reference","name":"SisTer Reference Subsystem","type":"Referencia controlada","status":"Validacao","contract":"sister.subsystem/1.0.0","access_mode":"authenticated_reverse_proxy","access_url":"/integrations/reference/"}
])";

constexpr std::string_view kFallbackDiagnostics = R"([
  {"service":"Contract Registry","status":"operacional","score":100},
  {"service":"Package Ingest","status":"em validacao","score":78},
  {"service":"Evidence Store","status":"operacional","score":92},
  {"service":"Territorial Catalog","status":"planejado","score":45},
  {"service":"API Server","status":"inicial","score":40},
  {"service":"PostgreSQL/pgvector","status":"planejado","score":20}
])";

ApiPayload routeApi(const std::string& path, AppState& state, const ServerConfig&) {
    constexpr std::string_view artifactPrefix = "/api/v1/engineering/artifacts/";
    if (path.starts_with(artifactPrefix)) {
        const auto relative = path.substr(artifactPrefix.size());
        const bool allowed = relative.starts_with("docs/") || relative.starts_with("contracts/") ||
            relative.starts_with("engineering/") || relative.starts_with("apps/") ||
            relative.starts_with("scripts/") || relative.starts_with("tests/") || relative.starts_with("storage/");
        if (!allowed || relative.find("..") != std::string_view::npos) return {false, false, "{}"};
        std::error_code error;
        const auto file = std::filesystem::weakly_canonical(std::filesystem::path(relative), error);
        if (error || !std::filesystem::is_regular_file(file, error) || error || std::filesystem::file_size(file, error) > 1024 * 1024) {
            return {false, false, "{}"};
        }
        std::ifstream input(file);
        std::ostringstream content;
        content << input.rdbuf();
        return {true, false, "{\"path\":\"" + jsonEscape(relative) + "\",\"content\":\"" + jsonEscape(content.str()) + "\"}"};
    }
    if (path == "/api/v1/engineering/plan") {
        std::ifstream input("engineering/planning/plan.json");
        if (!input) return {false, true, "{}"};
        std::ostringstream body;
        body << input.rdbuf();
        return {true, false, body.str()};
    }
    if (path == "/api/v1/engineering/operational-base/current") {
        if (auto body = state.db.queryOperationalBase()) return {true, false, *body};
        return {true, true,
            "{\"schema\":\"sister.operational-base/0.1.0\","
            "\"unavailable\":true,"
            "\"capability_source\":{\"source\":\"postgresql\",\"signed_contracts_verified\":false,"
            "\"verification_status\":\"database_unavailable\"},"
            "\"capabilities\":[],\"candidates\":[],"
            "\"assessment\":{\"status\":\"NOT_AVAILABLE\","
            "\"recommendation\":\"Conectar PostgreSQL e registrar contratos assinados de integração.\"}}"
        };
    }
    if (path == "/api/health") {
        std::lock_guard lock(state.dbMutex);
        const std::string dbStatus = state.db.connected() ? "connected" : "not_connected";
        return {true, false,
            "{\"status\":\"ok\",\"service\":\"sisterd\",\"version\":\"" SISTER_VERSION
            "\",\"database\":\"" +
            dbStatus + "\"}"};
    }

    if (path == "/api/systems") {
        return {true, false, std::string(kFallbackSystems)};
    }
    if (path == "/api/contracts") {
        return {true, false, std::string(kFallbackContracts)};
    }
    if (path == "/api/evidence") {
        std::lock_guard lock(state.dbMutex);
        if (auto result = state.db.queryEvidence()) return {true, false, *result};
        return {true, true, "[]"};
    }
    if (path == "/api/diagnostics") {
        std::lock_guard lock(state.dbMutex);
        if (auto result = state.db.queryDiagnostics()) return {true, false, *result};
        return {true, true, std::string(kFallbackDiagnostics)};
    }
    if (path == "/api/integrations/sister-reference") {
        return {true, false,
            R"({"contract_version":"1.0.0","system_id":"sister_reference","integration_state":"reference","operational_access":true,"access_url":"/integrations/reference/","access_mode":"authenticated_reverse_proxy","capabilities":["reference.identity.read","reference.echo.execute"]})"};
    }
    return {};
}

void sendResponse(int client, const HttpResponse& response, const ServerConfig& config,
                  std::string_view requestId, bool headOnly) {
    try {
        sendAll(client, serializeResponse(response, config, requestId, headOnly));
    } catch (const std::exception&) {
        // best-effort: ignore send errors
    }
}

void logAuthorizationDecision(
    const std::optional<sisterd::AuthUser>& actor,
    std::string_view capability,
    std::string_view resource,
    std::string_view purpose,
    std::string_view result,
    std::string_view reason,
    std::string_view requestId) {
    const auto timestampMilliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    std::lock_guard lock(gLogMutex);
    std::cerr << "level=info event=authorization"
              << " timestamp_ms=" << timestampMilliseconds
              << " request_id=" << logSafe(requestId)
              << " actor=" << logSafe(actor ? actor->id : "anonymous")
              << " role=" << logSafe(actor ? actor->role : "none")
              << " capability=" << logSafe(capability)
              << " resource=" << logSafe(resource)
              << " purpose=" << logSafe(purpose)
              << " result=" << logSafe(result)
              << " reason=" << logSafe(reason)
              << '\n';
}

bool authorizeOrReject(
    int client,
    const std::optional<sisterd::AuthUser>& actor,
    std::string_view capability,
    std::string_view resource,
    std::string_view purpose,
    const HttpRequest& request,
    const ServerConfig& config,
    std::string_view requestId,
    std::string_view peer,
    bool headOnly,
    Clock::time_point requestStart) {
    int status = 200;
    std::string_view reason = "capability_granted";
    if (!actor) {
        status = 401;
        reason = "authentication_required";
    } else if (capability.empty()) {
        status = 403;
        reason = "capability_not_declared";
    } else if (!hasCapability(*actor, capability)) {
        status = 403;
        reason = "capability_missing";
    }

    logAuthorizationDecision(
        actor, capability, resource, purpose,
        status == 200 ? "allow" : "deny", reason, requestId);
    if (status == 200) return true;

    sendResponse(
        client,
        status == 401
            ? jsonError(401, "Unauthorized", "Autenticação necessária.")
            : jsonError(403, "Forbidden", "Capacidade necessária não concedida."),
        config, requestId, headOnly);
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
    logEvent("info", requestId, peer, request.method, request.path, status, elapsed, reason);
    return false;
}

void handleClient(
    int clientFd,
    const std::string& peer,
    const std::string& remoteAddress,
    AppState& state,
    const ServerConfig& config,
    sisterd::security::LoginRateLimiter& rateLimiter) {
    const auto requestStart = Clock::now();
    const std::string requestId = randomHex(8);

    setSocketTimeouts(clientFd, config.clientTimeoutSeconds);

    auto result = readRequest(clientFd);
    if (!result.request) {
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("warn", requestId, peer, "-", "-", result.status, elapsed, result.detail);
        const HttpResponse errorResponse = jsonError(result.status, result.reason, result.detail);
        sendResponse(clientFd, errorResponse, config, requestId, false);
        return;
    }

    HttpRequest& request = *result.request;

    if (config.requireSameOrigin && !sameOriginRequest(request, config)) {
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("warn", requestId, peer, request.method, request.path, 403, elapsed, "cross-origin request rejected");
        sendResponse(clientFd, jsonError(403, "Forbidden", "Requisição de origem cruzada não permitida."),
                     config, requestId, false);
        return;
    }

    const bool isHead = request.method == "HEAD";
    const std::string sessionToken = cookieValue(request, kSessionCookie);

    // --- Auth API ---
    if (request.path == "/api/auth/bootstrap" && request.method == "GET") {
        if (!config.httpBootstrapEnabled) {
            const HttpResponse resp{200, "OK", R"({"open":false,"http_enabled":false})",
                "application/json; charset=utf-8", {{"Cache-Control", "no-store"}}};
            sendResponse(clientFd, resp, config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("info", requestId, peer, request.method, request.path, 200, elapsed,
                     "HTTP bootstrap disabled");
            return;
        }
        std::lock_guard lock(state.authMutex);
        const bool open = state.auth.bootstrapOpen();
        const HttpResponse resp{200, "OK",
            open ? R"({"open":true})" : R"({"open":false})",
            "application/json; charset=utf-8",
            {{"Cache-Control", "no-store"}}};
        sendResponse(clientFd, resp, config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 200, elapsed);
        return;
    }

    if (request.path == "/api/auth/register" && request.method == "POST") {
        if (!config.httpBootstrapEnabled) {
            sendResponse(clientFd,
                jsonError(403, "Forbidden", "Bootstrap administrativo HTTP desativado."),
                config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("warn", requestId, peer, request.method, request.path, 403, elapsed,
                     "HTTP bootstrap disabled");
            return;
        }
        const auto fields = parseFlatJsonObject(request.body);
        const auto name = fields ? jsonStringField(*fields, "name") : std::nullopt;
        const auto email = fields ? jsonStringField(*fields, "email") : std::nullopt;
        const auto password = fields ? jsonStringField(*fields, "password") : std::nullopt;
        if (!name || !email || !password) {
            sendResponse(clientFd, jsonError(400, "Bad Request", "Preencha nome, e-mail e senha."),
                         config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("warn", requestId, peer, request.method, request.path, 400, elapsed);
            return;
        }
        try {
            std::lock_guard lock(state.authMutex);
            const auto registered = state.auth.registerAdmin(*name, *email, *password);
            if (!registered) {
                sendResponse(clientFd,
                    jsonError(409, "Conflict", "O cadastro inicial já foi concluído ou os dados são inválidos."),
                    config, requestId, isHead);
                const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
                logEvent("warn", requestId, peer, request.method, request.path, 409, elapsed);
                return;
            }
            const HttpResponse resp{201, "Created", R"({"status":"authenticated"})",
                "application/json; charset=utf-8",
                sessionHeaders(registered->token, config)};
            sendResponse(clientFd, resp, config, requestId, isHead);
        } catch (const std::exception& ex) {
            sendResponse(clientFd,
                jsonError(500, "Internal Server Error", "Não foi possível criar a conta."),
                config, requestId, isHead);
        }
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 201, elapsed);
        return;
    }

    if (request.path == "/api/auth/login" && request.method == "POST") {
        const auto fields = parseFlatJsonObject(request.body);
        const auto email = fields ? jsonStringField(*fields, "email") : std::nullopt;
        const auto password = fields ? jsonStringField(*fields, "password") : std::nullopt;
        if (!email || !password) {
            sendResponse(clientFd, jsonError(400, "Bad Request", "Preencha e-mail e senha."),
                         config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("warn", requestId, peer, request.method, request.path, 400, elapsed);
            return;
        }
        const auto normalizedIdentity = sisterd::AuthStore::normalizeIdentity(*email);
        const auto rateDecision = rateLimiter.checkAndRecord(remoteAddress, normalizedIdentity);
        if (!rateDecision.allowed) {
            auto response = jsonError(
                429, "Too Many Requests", "Muitas tentativas de login. Aguarde alguns minutos.");
            response.headers.emplace_back(
                "Retry-After", std::to_string(rateDecision.retryAfter.count()));
            sendResponse(clientFd, response, config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent(
                "warn", requestId, peer, request.method, request.path, 429, elapsed,
                "rate_limited scope=" + rateDecision.scope +
                    " buckets=" + std::to_string(rateDecision.buckets) +
                    " rejections=" + std::to_string(rateDecision.rejections) +
                    " evictions=" + std::to_string(rateDecision.evictions));
            return;
        }
        try {
            std::lock_guard lock(state.authMutex);
            const auto logged = state.auth.login(*email, *password);
            if (!logged) {
                sendResponse(clientFd, jsonError(401, "Unauthorized", "Credenciais inválidas."),
                             config, requestId, isHead);
                const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
                logEvent("warn", requestId, peer, request.method, request.path, 401, elapsed, "invalid credentials");
                return;
            }
            const HttpResponse resp{200, "OK", R"({"status":"authenticated"})",
                "application/json; charset=utf-8",
                sessionHeaders(logged->token, config)};
            sendResponse(clientFd, resp, config, requestId, isHead);
        } catch (const std::exception&) {
            sendResponse(clientFd,
                jsonError(500, "Internal Server Error", "Não foi possível entrar."),
                config, requestId, isHead);
        }
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 200, elapsed);
        return;
    }

    if (request.path == "/api/auth/logout" && request.method == "POST") {
        {
            std::lock_guard lock(state.authMutex);
            state.auth.logout(sessionToken);
        }
        const HttpResponse resp{204, "No Content", {}, "application/json; charset=utf-8",
            clearSessionHeaders(config)};
        sendResponse(clientFd, resp, config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 204, elapsed);
        return;
    }

    // --- Session resolution ---
    std::optional<sisterd::AuthUser> actor;
    {
        std::lock_guard lock(state.authMutex);
        actor = state.auth.userForToken(sessionToken);
    }

    // --- Governed participation ---
    if (request.path == "/api/v1/participations" ||
        (request.path.starts_with("/api/v1/participations/") && request.method == "GET")) {
        const bool proposing = request.method == "POST" && request.path == "/api/v1/participations";
        const auto capability = proposing ? "participation.propose" : "participation.read";
        if (!authorizeOrReject(clientFd, actor, capability, "participation",
                "governed_participation", request, config, requestId, peer, isHead, requestStart)) return;
        if (proposing) {
            std::lock_guard lock(state.dbMutex);
            const auto field = [&](std::string_view name) -> std::string {
                const std::string marker = "\"" + std::string(name) + "\"";
                const auto at = request.body.find(marker);
                if (at == std::string::npos) return {};
                const auto colon = request.body.find(':', at + marker.size());
                const auto first = request.body.find('"', colon + 1);
                const auto last = request.body.find('"', first + 1);
                return colon == std::string::npos || first == std::string::npos || last == std::string::npos
                    ? std::string() : request.body.substr(first + 1, last - first - 1);
            };
            const std::optional<sisterd::AuthenticatedPrincipal> principal = actor
                ? std::optional<sisterd::AuthenticatedPrincipal>(sisterd::AuthenticatedPrincipal{actor->id, "AuthStore"})
                : std::nullopt;
            const auto result = state.participation.propose(
                principal ? &*principal : nullptr,
                request.body, field("participation_id"), field("participant_system_id"),
                field("contract_version"), field("contract_digest"), field("origin_commit"));
            if (std::holds_alternative<sisterd::ParticipationServiceError>(result)) {
                const auto& error = std::get<sisterd::ParticipationServiceError>(result);
                sendResponse(clientFd, jsonError(error.status, error.status == 503 ? "Service Unavailable" : "Bad Request", error.detail), config, requestId, isHead);
                return;
            }
            sendResponse(clientFd, HttpResponse{201, "Created", std::get<std::string>(result), "application/json; charset=utf-8", {}}, config, requestId, isHead);
            return;
        }
        const auto id = request.path.substr(std::string("/api/v1/participations/").size());
        if (id.empty() || id.find('/') != std::string::npos) {
            sendResponse(clientFd, jsonError(404, "Not Found", "Participação não encontrada."), config, requestId, isHead);
            return;
        }
        std::lock_guard lock(state.dbMutex);
        const auto result = state.participation.show(id);
        if (std::holds_alternative<sisterd::ParticipationServiceError>(result)) {
            const auto& error = std::get<sisterd::ParticipationServiceError>(result);
            sendResponse(clientFd, jsonError(error.status, error.status == 503 ? "Service Unavailable" : "Not Found", error.detail), config, requestId, isHead);
        } else {
            sendResponse(clientFd, HttpResponse{200, "OK", std::get<std::string>(result), "application/json; charset=utf-8", {}}, config, requestId, isHead);
        }
        return;
    }

    // --- Operational integration decisions ---
    constexpr std::string_view integrationDecisionPrefix = "/api/v1/engineering/integrations/";
    constexpr std::string_view integrationDecisionSuffix = "/decision";
    if (request.path.starts_with(integrationDecisionPrefix) &&
        request.path.ends_with(integrationDecisionSuffix)) {
        if (request.method != "POST") {
            sendResponse(clientFd, jsonError(405, "Method Not Allowed", "Método não permitido."),
                         config, requestId, isHead);
            return;
        }
        if (!authorizeOrReject(
                clientFd, actor, "engineering.integration.decide",
                "sister-operational-base", "integration_decision",
                request, config, requestId, peer, isHead, requestStart)) return;

        const auto encodedTarget = request.path.substr(
            integrationDecisionPrefix.size(),
            request.path.size() - integrationDecisionPrefix.size() -
                integrationDecisionSuffix.size());
        const auto separator = encodedTarget.rfind('/');
        if (separator == std::string::npos || separator == 0 ||
            separator + 1 >= encodedTarget.size()) {
            sendResponse(clientFd, jsonError(404, "Not Found", "Integração não encontrada."),
                         config, requestId, isHead);
            return;
        }
        const std::string integrationId = encodedTarget.substr(0, separator);
        const std::string version = encodedTarget.substr(separator + 1);
        const auto fields = parseFlatJsonObject(request.body);
        const auto decision = fields ? jsonStringField(*fields, "decision") : std::nullopt;
        const auto rationale = fields ? jsonStringField(*fields, "rationale") : std::nullopt;
        if (!decision || (*decision != "approved" && *decision != "rejected") ||
            !rationale || trim(*rationale).empty()) {
            sendResponse(clientFd, jsonError(400, "Bad Request", "Informe decision e rationale."),
                         config, requestId, isHead);
            return;
        }

        std::lock_guard lock(state.dbMutex);
        const auto result = state.db.decideIntegration(
            integrationId, version, *decision, actor->id, trim(*rationale));
        if (!result) {
            sendResponse(clientFd, jsonError(409, "Conflict", "Decisão de integração não aplicada."),
                         config, requestId, isHead);
            return;
        }
        sendResponse(clientFd, HttpResponse{
            200, "OK", *result, "application/json; charset=utf-8",
            {{"Cache-Control", "no-store"}}
        }, config, requestId, isHead);
        return;
    }

    constexpr std::string_view integrationExecuteSuffix = "/execute";
    if (request.path.starts_with(integrationDecisionPrefix) &&
        request.path.ends_with(integrationExecuteSuffix)) {
        if (request.method != "POST") {
            sendResponse(clientFd, jsonError(405, "Method Not Allowed", "Método não permitido."),
                         config, requestId, isHead);
            return;
        }
        if (!authorizeOrReject(
                clientFd, actor, "engineering.integration.execute",
                "sister-operational-base", "approved_integration_execution",
                request, config, requestId, peer, isHead, requestStart)) return;
        if (!config.referenceSubsystemEnabled) {
            sendResponse(clientFd, jsonError(503, "Service Unavailable", "Subsistema de referência indisponível."),
                         config, requestId, isHead);
            return;
        }

        const auto encodedTarget = request.path.substr(
            integrationDecisionPrefix.size(),
            request.path.size() - integrationDecisionPrefix.size() -
                integrationExecuteSuffix.size());
        const auto separator = encodedTarget.rfind('/');
        if (separator == std::string::npos || separator == 0 ||
            separator + 1 >= encodedTarget.size()) {
            sendResponse(clientFd, jsonError(404, "Not Found", "Integração não encontrada."),
                         config, requestId, isHead);
            return;
        }
        const std::string integrationId = encodedTarget.substr(0, separator);
        const std::string version = encodedTarget.substr(separator + 1);
        const auto fields = parseFlatJsonObject(request.body);
        const auto value = fields ? jsonStringField(*fields, "value") : std::nullopt;
        if (!value || value->empty()) {
            sendResponse(clientFd, jsonError(400, "Bad Request", "Informe value para executar a integração."),
                         config, requestId, isHead);
            return;
        }

        {
            std::lock_guard lock(state.dbMutex);
            if (!state.db.integrationApproved(integrationId, version)) {
                sendResponse(clientFd,
                    jsonError(409, "Conflict", "Integração não aprovada na Base Operacional."),
                    config, requestId, isHead);
                return;
            }
        }

        const std::string upstreamBody = "{\"value\":\"" + jsonEscape(*value) + "\"}";
        HttpRequest upstream = request;
        upstream.method = "POST";
        upstream.path = "/integrations/reference/echo";
        upstream.query.clear();
        upstream.body = upstreamBody;
        upstream.headers["content-type"] = "application/json";

        std::string observedValue;
        std::string observedExecutor;
        std::string rawBody;
        int proxyStatus = 502;
        try {
            const auto raw = proxyToSubsystem(
                upstream, *actor, "/integrations/reference", config.referencePort,
                "SisTer Reference Subsystem", requestId, config);
            proxyStatus = statusFromRawHttpResponse(raw);
            rawBody = rawHttpBody(raw);
            const auto observed = parseFlatJsonObject(rawBody);
            if (observed) {
                observedValue = jsonStringField(*observed, "value").value_or("");
                observedExecutor = jsonStringField(*observed, "processed_by").value_or("");
            }
        } catch (const std::exception& ex) {
            rawBody = "{\"error\":\"" + jsonEscape(ex.what()) + "\"}";
        }

        const bool confirmed = proxyStatus == 200 &&
            observedValue == *value && observedExecutor == "sister_reference";
        const std::string executionId = "exec-" + integrationId + "-" + randomHex(6);
        const std::string assessmentId = "oa-" + executionId;
        const std::string status = confirmed ? "completed" : "failed";
        const std::string result = confirmed ? "confirmed" : "divergent";
        const std::string recommendation = confirmed ? "none" : "request_human_decision";
        const bool humanDecisionRequired = !confirmed;
        const std::string executionJson =
            "{\"execution_id\":\"" + jsonEscape(executionId) + "\","
            "\"integration_id\":\"" + jsonEscape(integrationId) + "\","
            "\"integration_version\":\"" + jsonEscape(version) + "\","
            "\"status\":\"" + status + "\","
            "\"inputs\":[{\"reference_id\":\"request.value\","
            "\"schema_id\":\"sister.echo.request/1.0.0\","
            "\"digest\":\"sha256:" + sha256Hex(*value) + "\","
            "\"subsystem_id\":\"sister\"}],"
            "\"transformations_applied\":[\"enviar payload echo pelo SisTer\","
            "\"registrar resposta observada\"],"
            + (confirmed
                ? "\"outputs\":[{\"reference_id\":\"response.echo\","
                  "\"schema_id\":\"sister.subsystem.echo/1.0.0\","
                  "\"digest\":\"sha256:" + sha256Hex(rawBody) + "\","
                  "\"subsystem_id\":\"sister_reference\"}],"
                  "\"observations\":[\"observed_value igual a expected_value\","
                  "\"executor observado igual a sister_reference\"]"
                : "\"errors\":[{\"code\":\"OBSERVED_DIVERGENCE\","
                  "\"message\":\"Resposta observada diverge do esperado ou execução falhou\"}],"
                  "\"observations\":[\"execução não confirmou os critérios aprovados\"]")
            + "}";
        const std::string assessmentJson =
            "{\"assessment_id\":\"" + jsonEscape(assessmentId) + "\","
            "\"integration_id\":\"" + jsonEscape(integrationId) + "\","
            "\"execution_id\":\"" + jsonEscape(executionId) + "\","
            "\"expected\":[\"requisição mediada pelo SisTer\","
            "\"resposta segue sister.subsystem.echo/1.0.0\","
            "\"observed_value igual a expected_value\","
            "\"executor observado igual a sister_reference\"],"
            "\"observed\":[\"status HTTP " + std::to_string(proxyStatus) + "\","
            "\"observed_value=" + jsonEscape(observedValue) + "\","
            "\"executor=" + jsonEscape(observedExecutor) + "\"],"
            "\"result\":\"" + result + "\","
            "\"severity\":\"" + (confirmed ? "informational" : "medium") + "\","
            "\"recommendation\":{\"action\":\"" + recommendation + "\","
            "\"summary\":\"" + (confirmed
                ? "Execução compatível com os critérios aprovados."
                : "Engenharia deve revisar contrato, disponibilidade ou mapeamento antes de nova execução.") + "\"},"
            "\"human_decision_required\":" + std::string(humanDecisionRequired ? "true" : "false") + "}";

        std::lock_guard lock(state.dbMutex);
        const auto recorded = state.db.recordIntegrationExecution(
            integrationId, version, executionId, status,
            "sha256:" + sha256Hex(executionJson), executionJson,
            assessmentId, result, recommendation, humanDecisionRequired,
            assessmentJson);
        if (!recorded) {
            sendResponse(clientFd, jsonError(409, "Conflict", "Execução não registrada na Base Operacional."),
                         config, requestId, isHead);
            return;
        }
        sendResponse(clientFd, HttpResponse{
            200, "OK", *recorded, "application/json; charset=utf-8",
            {{"Cache-Control", "no-store"}}
        }, config, requestId, isHead);
        return;
    }

    // --- Controlled reference subsystem: normative integration target ---
    if (request.path == "/integrations/reference" ||
        request.path.starts_with("/integrations/reference/")) {
        if (!config.referenceSubsystemEnabled) {
            sendResponse(clientFd, jsonError(404, "Not Found", "Recurso não encontrado."),
                         config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("warn", requestId, peer, request.method, request.path, 404, elapsed,
                     "reference subsystem disabled by execution profile");
            return;
        }
        if (request.path == "/integrations/reference") {
            if (!authorizeOrReject(
                    clientFd, actor, "reference.identity.read", "sister-reference",
                    "platform_validation", request, config, requestId, peer, isHead, requestStart)) return;
            sendResponse(clientFd,
                         redirectResponse(308, "Permanent Redirect", "/integrations/reference/identity"),
                         config, requestId, isHead);
            return;
        }

        const bool canonicalRead = request.method == "GET" && (
            request.path == "/integrations/reference/manifest" ||
            request.path == "/integrations/reference/health" ||
            request.path == "/integrations/reference/ready" ||
            request.path == "/integrations/reference/capabilities" ||
            request.path == "/integrations/reference/identity");
        const bool compatibilityRead = request.method == "GET" && (
            request.path == "/integrations/reference/api/identity" ||
            request.path == "/integrations/reference/api/whoami" ||
            request.path.starts_with("/integrations/reference/_sister/"));
        const bool echoExecute = request.method == "POST" &&
            (request.path == "/integrations/reference/echo" ||
             request.path == "/integrations/reference/api/echo");
        if (!canonicalRead && !compatibilityRead && !echoExecute) {
            sendResponse(clientFd, jsonError(404, "Not Found", "Recurso não encontrado."),
                         config, requestId, isHead);
            return;
        }
        const std::string_view capability = (canonicalRead || compatibilityRead)
            ? "reference.identity.read" : "reference.echo.execute";
        if (!authorizeOrReject(
                clientFd, actor, capability, "sister-reference", "platform_validation",
                request, config, requestId, peer, isHead, requestStart)) return;
        try {
            const auto raw = proxyToSubsystem(
                request, *actor, "/integrations/reference", config.referencePort,
                "SisTer Reference Subsystem", requestId, config);
            sendAll(clientFd, raw);
            const auto proxyStatus = statusFromRawHttpResponse(raw);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("info", requestId, peer, request.method, request.path, proxyStatus, elapsed);
        } catch (const std::exception& ex) {
            sendResponse(clientFd,
                jsonError(502, "Bad Gateway", "Subsistema de referência indisponível."),
                config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("warn", requestId, peer, request.method, request.path, 502, elapsed, ex.what());
        }
        return;
    }

    // --- /api/me ---
    if (request.path == "/api/me/capabilities") {
        if (!authorizeOrReject(
                clientFd, actor, "session.self.read", "current-session",
                "self_service", request, config, requestId, peer, isHead, requestStart)) return;
        const HttpResponse resp{200, "OK", jsonCapabilities(*actor),
            "application/json; charset=utf-8", {{"Cache-Control", "no-store"}}};
        sendResponse(clientFd, resp, config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 200, elapsed);
        return;
    }

    if (request.path == "/api/me") {
        if (!authorizeOrReject(
                clientFd, actor, "session.self.read", "current-session",
                "self_service", request, config, requestId, peer, isHead, requestStart)) return;
        const HttpResponse resp{200, "OK", jsonUser(*actor),
            "application/json; charset=utf-8", {{"Cache-Control", "no-store"}}};
        sendResponse(clientFd, resp, config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 200, elapsed);
        return;
    }

    // --- /api/admin/maturity ---
    if (request.path == "/api/admin/maturity/latest" ||
        request.path == "/api/admin/maturity/history" ||
        request.path == "/api/admin/maturity/components" ||
        request.path == "/api/admin/maturity/catalog" ||
        request.path == "/api/admin/maturity/quality") {
        if (request.method != "GET" && request.method != "HEAD") {
            sendResponse(clientFd, jsonError(405, "Method Not Allowed", "Método não permitido."),
                         config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("warn", requestId, peer, request.method, request.path, 405, elapsed);
            return;
        }
        if (!authorizeOrReject(
                clientFd, actor, "maturity.evidence.read", "sister-maturity",
                "engineering_governance", request, config, requestId, peer, isHead, requestStart)) return;

        if (request.path == "/api/admin/maturity/components") {
            auto routeResp = sisterd::api::getMaturityComponents(config.maturityRoot);
            const HttpResponse response{routeResp.status_code, routeResp.reason_phrase, routeResp.body, routeResp.content_type, {{"Cache-Control", "no-store"}}};
            sendResponse(clientFd, response, config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent(routeResp.status_code >= 400 ? "warn" : "info", requestId, peer, request.method, request.path, routeResp.status_code, elapsed);
            return;
        }
        if (request.path == "/api/admin/maturity/catalog") {
            auto routeResp = sisterd::api::getMaturityCatalog(config.maturityRoot);
            const HttpResponse response{routeResp.status_code, routeResp.reason_phrase, routeResp.body, routeResp.content_type, {{"Cache-Control", "no-store"}}};
            sendResponse(clientFd, response, config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent(routeResp.status_code >= 400 ? "warn" : "info", requestId, peer, request.method, request.path, routeResp.status_code, elapsed);
            return;
        }
        if (request.path == "/api/admin/maturity/quality") {
            auto routeResp = sisterd::api::getQualityStatus(config.maturityRoot);
            const HttpResponse response{routeResp.status_code, routeResp.reason_phrase, routeResp.body, routeResp.content_type, {{"Cache-Control", "no-store"}}};
            sendResponse(clientFd, response, config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent(routeResp.status_code >= 400 ? "warn" : "info", requestId, peer, request.method, request.path, routeResp.status_code, elapsed);
            return;
        }

        const bool latest = request.path.ends_with("/latest");
        const auto document = readFixedJsonDocument(
            latest ? config.maturityRoot / "latest.json" : config.maturityRoot / "history" / "index.json",
            latest ? "sister.maturity-status/1.0.0" : "sister.maturity-history/1.0.0");
        if (document.state == FixedJsonState::Missing) {
            sendResponse(clientFd, jsonError(404, "Not Found", "Nenhuma evidência de maturidade foi publicada."),
                         config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("info", requestId, peer, request.method, request.path, 404, elapsed);
            return;
        }
        if (document.state == FixedJsonState::Invalid) {
            sendResponse(clientFd, jsonError(503, "Service Unavailable", "A evidência de maturidade publicada é inválida."),
                         config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("warn", requestId, peer, request.method, request.path, 503, elapsed, "invalid maturity document");
            return;
        }

        const HttpResponse response{200, "OK", document.body, "application/json; charset=utf-8",
            {{"Cache-Control", "no-store"}}};
        sendResponse(clientFd, response, config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 200, elapsed);
        return;
    }

    // --- /api/admin/users ---
    if (request.path == "/api/admin/users" || request.path.starts_with("/api/admin/users/")) {
        if (!authorizeOrReject(
                clientFd, actor, "identity.users.manage", "sister-identities",
                "identity_administration", request, config, requestId, peer, isHead, requestStart)) return;

        const bool isBase = (request.path == "/api/admin/users");
        const std::string targetId = isBase ? "" : request.path.substr(std::string("/api/admin/users/").size());

        if (isBase && request.method == "GET") {
            std::lock_guard lock(state.authMutex);
            const auto users = state.auth.users();
            std::string body = "[";
            for (std::size_t index = 0; index < users.size(); ++index) {
                if (index > 0) body += ',';
                body += jsonUser(users[index]);
            }
            body += ']';
            const HttpResponse resp{200, "OK", body, "application/json; charset=utf-8",
                {{"Cache-Control", "no-store"}}};
            sendResponse(clientFd, resp, config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("info", requestId, peer, request.method, request.path, 200, elapsed);
            return;
        }

        if (isBase && request.method == "POST") {
            const auto fields = parseFlatJsonObject(request.body);
            const auto name = fields ? jsonStringField(*fields, "name") : std::nullopt;
            const auto email = fields ? jsonStringField(*fields, "email") : std::nullopt;
            const auto password = fields ? jsonStringField(*fields, "password") : std::nullopt;
            const auto role = fields ? jsonStringField(*fields, "role") : std::nullopt;
            if (!name || !email || !password || !role) {
                sendResponse(clientFd, jsonError(400, "Bad Request", "Preencha todos os campos."),
                             config, requestId, isHead);
                const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
                logEvent("warn", requestId, peer, request.method, request.path, 400, elapsed);
                return;
            }
            try {
                std::lock_guard lock(state.authMutex);
                std::string errorDetail;
                const auto created = state.auth.createUser(*name, *email, *password, *role, &errorDetail);
                if (!created) {
                    const int statusCode = (errorDetail == "E-mail já cadastrado.") ? 409 : 400;
                    sendResponse(clientFd,
                        jsonError(statusCode, statusCode == 409 ? "Conflict" : "Bad Request",
                            errorDetail.empty() ? "Dados inválidos para cadastro." : errorDetail),
                        config, requestId, isHead);
                    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
                    logEvent("warn", requestId, peer, request.method, request.path, statusCode, elapsed, errorDetail);
                    return;
                }
                const HttpResponse resp{201, "Created", jsonUser(*created),
                    "application/json; charset=utf-8", {{"Cache-Control", "no-store"}}};
                sendResponse(clientFd, resp, config, requestId, isHead);
            } catch (const std::exception&) {
                sendResponse(clientFd,
                    jsonError(500, "Internal Server Error", "Não foi possível criar a conta."),
                    config, requestId, isHead);
            }
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("info", requestId, peer, request.method, request.path, 201, elapsed);
            return;
        }

        if (!isBase && !targetId.empty() && (request.method == "PUT" || request.method == "PATCH")) {
            const auto fields = parseFlatJsonObject(request.body);
            const auto name = fields ? jsonStringField(*fields, "name") : std::nullopt;
            const auto email = fields ? jsonStringField(*fields, "email") : std::nullopt;
            const auto role = fields ? jsonStringField(*fields, "role") : std::nullopt;
            const auto password = fields ? jsonStringField(*fields, "password").value_or("") : std::string{};
            if (!name || !email || !role) {
                sendResponse(clientFd,
                    jsonError(400, "Bad Request", "Preencha todos os campos obrigatórios."),
                    config, requestId, isHead);
                const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
                logEvent("warn", requestId, peer, request.method, request.path, 400, elapsed);
                return;
            }
            try {
                std::lock_guard lock(state.authMutex);
                std::string errorDetail;
                const auto updated = state.auth.updateUser(targetId, *name, *email, *role, password, &errorDetail);
                if (!updated) {
                    const int statusCode = (errorDetail == "Usuário não encontrado.") ? 404 :
                                           (errorDetail.find("já cadastrado") != std::string::npos) ? 409 : 400;
                    sendResponse(clientFd,
                        jsonError(statusCode,
                            statusCode == 404 ? "Not Found" : statusCode == 409 ? "Conflict" : "Bad Request",
                            errorDetail.empty() ? "Dados inválidos para atualização." : errorDetail),
                        config, requestId, isHead);
                    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
                    logEvent("warn", requestId, peer, request.method, request.path, statusCode, elapsed, errorDetail);
                    return;
                }
                const HttpResponse resp{200, "OK", jsonUser(*updated),
                    "application/json; charset=utf-8", {{"Cache-Control", "no-store"}}};
                sendResponse(clientFd, resp, config, requestId, isHead);
            } catch (const std::exception&) {
                sendResponse(clientFd,
                    jsonError(500, "Internal Server Error", "Não foi possível atualizar a conta."),
                    config, requestId, isHead);
            }
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("info", requestId, peer, request.method, request.path, 200, elapsed);
            return;
        }

        if (!isBase && !targetId.empty() && request.method == "DELETE") {
            try {
                std::lock_guard lock(state.authMutex);
                std::string errorDetail;
                const bool deleted = state.auth.deleteUser(targetId, actor->id, &errorDetail);
                if (!deleted) {
                    const int statusCode = (errorDetail == "Usuário não encontrado.") ? 404 : 400;
                    sendResponse(clientFd,
                        jsonError(statusCode, statusCode == 404 ? "Not Found" : "Bad Request",
                            errorDetail.empty() ? "Não foi possível excluir o usuário." : errorDetail),
                        config, requestId, isHead);
                    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
                    logEvent("warn", requestId, peer, request.method, request.path, statusCode, elapsed, errorDetail);
                    return;
                }
                const HttpResponse resp{200, "OK", R"({"status":"deleted"})",
                    "application/json; charset=utf-8", {{"Cache-Control", "no-store"}}};
                sendResponse(clientFd, resp, config, requestId, isHead);
            } catch (const std::exception&) {
                sendResponse(clientFd,
                    jsonError(500, "Internal Server Error", "Não foi possível excluir a conta."),
                    config, requestId, isHead);
            }
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("info", requestId, peer, request.method, request.path, 200, elapsed);
            return;
        }

        sendResponse(clientFd, jsonError(405, "Method Not Allowed", "Método não permitido."),
                     config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("warn", requestId, peer, request.method, request.path, 405, elapsed);
        return;
    }

    // --- General API routes ---
    if (request.path.starts_with("/api/")) {
        if (request.method != "GET" && request.method != "HEAD") {
            sendResponse(clientFd, jsonError(405, "Method Not Allowed", "Método não permitido."),
                         config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("warn", requestId, peer, request.method, request.path, 405, elapsed);
            return;
        }

        const bool publicApi = request.path == "/api/health";
        if (!publicApi) {
            std::string_view capability;
            std::string_view resource = "sister-control-plane";
            std::string_view purpose = "governed_api_access";
            if (request.path == "/api/systems") capability = "subsystem.manifest.read";
            else if (request.path == "/api/v1/engineering/operational-base/current") {
                capability = "engineering.operational-base.read";
            }
            else if (request.path == "/api/v1/engineering/plan" ||
                     request.path.starts_with("/api/v1/engineering/artifacts/")) capability = "engineering.plan.read";
            else if (request.path == "/api/contracts") capability = "sister.governance.read";
            else if (request.path == "/api/evidence") capability = "sister.evidence.read";
            else if (request.path == "/api/diagnostics") capability = "sister.diagnostics.read";
            else if (request.path == "/api/integrations/sister-reference") {
                capability = "reference.identity.read";
                resource = "sister-reference";
                purpose = "platform_validation";
            }

            if (!authorizeOrReject(
                    clientFd, actor, capability, resource, purpose, request, config,
                    requestId, peer, isHead, requestStart)) return;
        }

        const auto payload = routeApi(request.path, state, config);
        if (!payload.found) {
            sendResponse(clientFd, jsonError(404, "Not Found", "Recurso não encontrado."),
                         config, requestId, isHead);
            const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
            logEvent("warn", requestId, peer, request.method, request.path, 404, elapsed);
            return;
        }

        const std::string cacheControl = publicApi ? "no-cache" : "no-store";
        const HttpResponse resp{200, "OK", payload.body, "application/json; charset=utf-8",
            {{"Cache-Control", cacheControl}}};
        sendResponse(clientFd, resp, config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 200, elapsed,
                 payload.fallback ? "fallback" : "");
        return;
    }

    // --- Static files ---
    if (request.method != "GET" && request.method != "HEAD") {
        sendResponse(clientFd, jsonError(405, "Method Not Allowed", "Método não permitido."),
                     config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("warn", requestId, peer, request.method, request.path, 405, elapsed);
        return;
    }

    if (request.path == "/login" && actor) {
        sendResponse(clientFd, redirectResponse(303, "See Other", "/"),
                     config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 303, elapsed);
        return;
    }

    if (request.path == "/admin/users" || request.path == "/admin/maturity") {
        const std::string_view capability = request.path == "/admin/users"
            ? "identity.users.manage" : "maturity.evidence.read";
        const std::string_view resource = request.path == "/admin/users"
            ? "sister-identities" : "sister-maturity";
        if (!authorizeOrReject(
                clientFd, actor, capability, resource, "administrative_interface",
                request, config, requestId, peer, isHead, requestStart)) return;
    }

    if (request.path.ends_with("/app.js") && !actor) {
        sendResponse(clientFd, jsonError(401, "Unauthorized", "Autenticação necessária."),
                     config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 401, elapsed);
        return;
    }

    const auto staticPath = resolveStaticPath(request.path, config);
    if (!staticPath) {
        sendResponse(clientFd, jsonError(404, "Not Found", "Página não encontrada."),
                     config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 404, elapsed);
        return;
    }

    try {
        const auto body = readFile(*staticPath);
        std::vector<std::pair<std::string, std::string>> extraHeaders;
        if (shouldNeverCacheStaticFile(*staticPath)) {
            extraHeaders.push_back({"Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"});
            extraHeaders.push_back({"Pragma", "no-cache"});
            extraHeaders.push_back({"Expires", "0"});
            if (shouldClearBrowserSiteData(*staticPath)) {
                extraHeaders.push_back({"Clear-Site-Data", "\"cache\", \"storage\""});
            }
        } else {
            extraHeaders.push_back({"Cache-Control", "public, max-age=3600"});
        }
        const HttpResponse resp{200, "OK", body, contentType(*staticPath), std::move(extraHeaders)};
        sendResponse(clientFd, resp, config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("info", requestId, peer, request.method, request.path, 200, elapsed);
    } catch (const std::exception& ex) {
        sendResponse(clientFd, jsonError(404, "Not Found", "Página não encontrada."),
                     config, requestId, isHead);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - requestStart);
        logEvent("warn", requestId, peer, request.method, request.path, 404, elapsed, ex.what());
    }
}

} // namespace

int main(int argc, char** argv) {
    ServerConfig config;
    try {
        config = loadConfig(argc, argv);
    } catch (const std::exception& ex) {
        std::cerr << "configuration error: " << ex.what() << '\n';
        return 1;
    }

    std::signal(SIGPIPE, SIG_IGN);
    std::signal(SIGINT, handleSignal);
    std::signal(SIGTERM, handleSignal);

    sisterd::runtime::Listener acquiredListener;
    try {
        acquiredListener = config.activatedUnixListener
            ? sisterd::runtime::acquireActivatedUnixListener(
                config.activatedSocketPath.string(), config.production)
            : sisterd::runtime::createTcpLoopbackListener(
                config.bindHost, config.port, config.queueLimit);
    } catch (const std::exception& ex) {
        std::cerr << "listener error: " << ex.what() << '\n';
        return 1;
    }
    UniqueFd server(acquiredListener.fd);

    AppState state(config.authFile, config.databaseUrl);
    sisterd::security::LoginRateLimiter rateLimiter;

    {
        std::lock_guard lock(gLogMutex);
        std::cerr << "level=info sisterd listening on "
                  << acquiredListener.description
                  << " web_root=" << config.canonicalWebRoot.string()
                  << " workers=" << config.workerThreads
                  << " env=" << (config.production ? "production" : "development")
                  << " http_bootstrap=" << (config.httpBootstrapEnabled ? "enabled" : "disabled")
                  << " legacy_proxy=" << (config.legacyProxyEnabled ? "enabled" : "disabled")
                  << " legacy_websocket_proxy="
                  << (config.legacyWebSocketProxyEnabled ? "enabled" : "disabled")
                  << '\n';
    }

    sisterd::runtime::ConnectionThreadPool pool(
        config.workerThreads, config.queueLimit,
        [&state, &config, &rateLimiter](
            const sisterd::runtime::ConnectionThreadPool::Job& job) {
            handleClient(
                job.client, job.peer, job.remoteAddress,
                state, config, rateLimiter);
        },
        [](std::string_view detail) { logUnhandledWorkerException(detail); });

    while (gKeepRunning) {
        fd_set readSet;
        FD_ZERO(&readSet);
        FD_SET(server.get(), &readSet);

        timeval timeout{};
        timeout.tv_sec = 1;
        const int ready = select(server.get() + 1, &readSet, nullptr, nullptr, &timeout);
        if (ready < 0) {
            if (errno == EINTR) continue;
            std::cerr << "select failed: " << std::strerror(errno) << '\n';
            break;
        }
        if (ready == 0) continue;

        sockaddr_storage clientAddress{};
        socklen_t clientLength = sizeof(clientAddress);
        const int clientFd = accept(
            server.get(), reinterpret_cast<sockaddr*>(&clientAddress), &clientLength);
        if (clientFd < 0) {
            if (errno == EINTR) continue;
            std::cerr << "accept failed: " << std::strerror(errno) << '\n';
            break;
        }

        std::string peer;
        std::string remoteAddress;
        if (acquiredListener.unixSocket) {
            peer = "unix-gateway";
            remoteAddress = "unix-gateway";
        } else {
            const auto* ipv4 = reinterpret_cast<const sockaddr_in*>(&clientAddress);
            char peerBuf[INET_ADDRSTRLEN] = {};
            if (clientAddress.ss_family != AF_INET ||
                inet_ntop(AF_INET, &ipv4->sin_addr, peerBuf, sizeof(peerBuf)) == nullptr) {
                close(clientFd);
                std::cerr << "level=warn detail=\"connection rejected: unexpected peer family\"\n";
                continue;
            }
            remoteAddress = peerBuf;
            peer = remoteAddress + ':' + std::to_string(ntohs(ipv4->sin_port));
        }

        if (!pool.submit({clientFd, peer, remoteAddress})) {
            close(clientFd);
            std::lock_guard lock(gLogMutex);
            std::cerr << "level=warn detail=\"connection rejected: queue full\" peer=\"" << peer << "\"\n";
        }
    }

    pool.stop();
    std::cerr << "level=info sisterd shutdown complete\n";
    return 0;
}
