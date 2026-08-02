# HAProxy de laboratório — SEC-03B

Este diretório contém somente fontes versionadas. Configuração renderizada,
certificados, chaves, PID e logs pertencem a `.run/gateway/`, que é ignorado
pelo Git.

O template materializa apenas a primeira fatia de SEC-03B:

- listener `127.0.0.1:8443`, TLS 1.3 e HTTP/1.1;
- Host único e métodos em allowlist;
- destino literal `127.0.0.1:8000`;
- rejeição de `Transfer-Encoding`, `Content-Length` duplicado, Upgrade e
  WebSocket;
- limites declarados de corpo;
- remoção dos headers externos governados e criação de novo request ID;
- health check do `sisterd`.

Não contém rate limiting, isolamento por usuário/cgroup, confiança do `sisterd`
nos headers, limite de resposta ou taxa mínima. Lua, plugins, resolvers,
destinos dinâmicos e backends controlados pelo cliente são proibidos.

Renderização e validação:

```bash
export GATEWAY_HAPROXY_BIN=/caminho/absoluto/para/haproxy-3.2.x
export GATEWAY_TLS_PEM="$PWD/.run/gateway/gateway-lab.pem"
export GATEWAY_ALLOWED_HOST=sister-gateway.test
export GATEWAY_CANONICAL_HOST=sister-gateway.test

python3 scripts/render_gateway_config.py
scripts/validate_gateway_config.sh
```

O binário deve pertencer à linha 3.2 e ser 3.2.22 ou posterior. O renderizador
recusa caminhos relativos, permissões excessivas, interface pública, porta 443
no laboratório, wildcard de Host, upstream alternativo e placeholders
residuais. A validação offline usa `haproxy -c -V` e não inicia processo.
