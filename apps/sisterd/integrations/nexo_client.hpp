#pragma once

#include "integration_client.hpp"

namespace sisterd::integrations {

class NexoClient final : public IntegrationClient {
public:
    explicit NexoClient(IntegrationClientConfig config);
    [[nodiscard]] std::string execute(const AuthorizedIntegrationRequest& request) const override;

private:
    IntegrationClientConfig config_;
};

} // namespace sisterd::integrations
