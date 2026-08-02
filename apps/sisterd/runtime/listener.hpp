#pragma once

#include <cstddef>
#include <string>
#include <string_view>

namespace sisterd::runtime {

struct Listener {
    int fd = -1;
    bool unixSocket = false;
    std::string description;
};

Listener createTcpLoopbackListener(
    std::string_view host,
    int port,
    std::size_t backlog);

Listener acquireActivatedUnixListener(
    std::string_view expectedPath,
    bool validateProductionPermissions = false);

} // namespace sisterd::runtime
