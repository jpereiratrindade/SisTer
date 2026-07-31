#pragma once

#include <string>

namespace sisterd {

// Returns a sanitized integration view. Secrets, paths and raw transport errors
// never cross this boundary.
std::string sisterStudioIntegrationJson();

} // namespace sisterd
