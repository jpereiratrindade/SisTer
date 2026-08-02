#include "listener.hpp"

#include <arpa/inet.h>
#include <fcntl.h>
#include <grp.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <unistd.h>

#include <cerrno>
#include <charconv>
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string>

namespace sisterd::runtime {
namespace {

constexpr int kActivatedDescriptor = 3;

class GuardedFd {
public:
    explicit GuardedFd(int fd) noexcept : fd_(fd) {}
    ~GuardedFd() {
        if (fd_ >= 0) close(fd_);
    }
    GuardedFd(const GuardedFd&) = delete;
    GuardedFd& operator=(const GuardedFd&) = delete;
    int release() noexcept {
        const int result = fd_;
        fd_ = -1;
        return result;
    }

private:
    int fd_;
};

long parseEnvironmentInteger(const char* name) {
    const char* raw = std::getenv(name);
    if (raw == nullptr || *raw == '\0') {
        throw std::runtime_error(std::string("missing socket activation variable: ") + name);
    }
    long result = 0;
    const char* end = raw + std::strlen(raw);
    const auto [pointer, error] = std::from_chars(raw, end, result);
    if (error != std::errc{} || pointer != end || result < 0) {
        throw std::runtime_error(std::string("invalid socket activation variable: ") + name);
    }
    return result;
}

void clearActivationEnvironment() {
    unsetenv("LISTEN_PID");
    unsetenv("LISTEN_FDS");
    unsetenv("LISTEN_FDNAMES");
}

[[noreturn]] void activationError(std::string_view detail);

void validateProductionPath(std::string_view expectedPath) {
    const struct group* gatewayGroup = getgrnam("haproxy");
    if (gatewayGroup == nullptr) activationError("required haproxy group does not exist");

    struct stat directoryStat {};
    if (lstat("/run/sister", &directoryStat) < 0 || !S_ISDIR(directoryStat.st_mode) ||
        directoryStat.st_uid != 0 || directoryStat.st_gid != gatewayGroup->gr_gid ||
        (directoryStat.st_mode & 0777) != 0750) {
        activationError("/run/sister ownership or mode is not root:haproxy 0750");
    }

    struct stat pathStat {};
    if (lstat(std::string(expectedPath).c_str(), &pathStat) < 0 || !S_ISSOCK(pathStat.st_mode) ||
        pathStat.st_uid != geteuid() || pathStat.st_gid != gatewayGroup->gr_gid ||
        (pathStat.st_mode & 0777) != 0660) {
        activationError("socket ownership or mode is not service-user:haproxy 0660");
    }
}

[[noreturn]] void activationError(std::string_view detail) {
    clearActivationEnvironment();
    throw std::runtime_error("invalid activated Unix listener: " + std::string(detail));
}

} // namespace

Listener createTcpLoopbackListener(
    std::string_view host,
    int port,
    std::size_t backlog) {
    const int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        throw std::runtime_error("TCP listener socket failed: " + std::string(std::strerror(errno)));
    }
    GuardedFd owned(fd);

    int enabled = 1;
    if (setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &enabled, sizeof(enabled)) < 0) {
        throw std::runtime_error("TCP listener setsockopt failed: " + std::string(std::strerror(errno)));
    }

    sockaddr_in address{};
    address.sin_family = AF_INET;
    if (inet_pton(AF_INET, std::string(host).c_str(), &address.sin_addr) != 1 ||
        (ntohl(address.sin_addr.s_addr) & 0xff000000u) != 0x7f000000u) {
        throw std::runtime_error("development TCP listener requires an IPv4 loopback address");
    }
    address.sin_port = htons(static_cast<uint16_t>(port));
    if (bind(fd, reinterpret_cast<sockaddr*>(&address), sizeof(address)) < 0) {
        throw std::runtime_error("TCP listener bind failed: " + std::string(std::strerror(errno)));
    }
    if (listen(fd, static_cast<int>(backlog)) < 0) {
        throw std::runtime_error("TCP listener listen failed: " + std::string(std::strerror(errno)));
    }
    return {owned.release(), false, "http://" + std::string(host) + ':' + std::to_string(port)};
}

Listener acquireActivatedUnixListener(
    std::string_view expectedPath,
    bool validateProductionPermissions) {
    if (expectedPath.empty() || expectedPath.front() != '/') {
        throw std::runtime_error("activated Unix listener path must be absolute");
    }

    const long listenPid = parseEnvironmentInteger("LISTEN_PID");
    const long listenFds = parseEnvironmentInteger("LISTEN_FDS");
    if (listenPid != static_cast<long>(getpid())) activationError("LISTEN_PID does not match process");
    if (listenFds != 1) activationError("exactly one descriptor is required");

    const char* descriptorNames = std::getenv("LISTEN_FDNAMES");
    if (descriptorNames != nullptr && std::string_view(descriptorNames) != "sisterd-http") {
        activationError("unexpected descriptor name");
    }

    if (fcntl(kActivatedDescriptor, F_GETFD) < 0) activationError("descriptor 3 is not open");

    int type = 0;
    socklen_t optionLength = sizeof(type);
    if (getsockopt(kActivatedDescriptor, SOL_SOCKET, SO_TYPE, &type, &optionLength) < 0 ||
        type != SOCK_STREAM) {
        activationError("descriptor is not SOCK_STREAM");
    }
    int accepting = 0;
    optionLength = sizeof(accepting);
    if (getsockopt(kActivatedDescriptor, SOL_SOCKET, SO_ACCEPTCONN, &accepting, &optionLength) < 0 ||
        accepting != 1) {
        activationError("descriptor is not listening");
    }

    struct stat descriptorStat {};
    if (fstat(kActivatedDescriptor, &descriptorStat) < 0 || !S_ISSOCK(descriptorStat.st_mode)) {
        activationError("descriptor is not a socket inode");
    }

    sockaddr_un address{};
    socklen_t addressLength = sizeof(address);
    if (getsockname(
            kActivatedDescriptor,
            reinterpret_cast<sockaddr*>(&address),
            &addressLength) < 0 ||
        address.sun_family != AF_UNIX) {
        activationError("descriptor is not AF_UNIX");
    }
    if (address.sun_path[0] == '\0') activationError("abstract Unix sockets are forbidden");
    const std::size_t maximumPathLength = sizeof(address.sun_path);
    const std::string observedPath(address.sun_path, strnlen(address.sun_path, maximumPathLength));
    if (observedPath != expectedPath) activationError("socket path does not match the configured path");
    if (validateProductionPermissions) validateProductionPath(expectedPath);

    const int flags = fcntl(kActivatedDescriptor, F_GETFD);
    if (flags < 0 || fcntl(kActivatedDescriptor, F_SETFD, flags | FD_CLOEXEC) < 0) {
        activationError("could not set close-on-exec");
    }
    clearActivationEnvironment();
    return {kActivatedDescriptor, true, "unix:" + observedPath};
}

} // namespace sisterd::runtime
