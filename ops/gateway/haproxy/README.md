# HAProxy de laboratório — SEC-03B

Este diretório contém somente fontes versionadas. Configuração renderizada,
certificados, chaves, PID e logs pertencem a `.run/gateway/`, que é ignorado
pelo Git.

O template materializa apenas a primeira fatia de SEC-03B:

- listener `127.0.0.1:8443`, TLS 1.3 e HTTP/1.1;
- Host único e métodos em allowlist;
- destino literal `127.0.0.1:8000`;
- regras de rejeição para `Transfer-Encoding`, `Content-Length` duplicado,
  Upgrade e WebSocket, sujeitas aos resultados de normalização documentados em
  `docs/evidence/security/SEC-03B.md`;
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

Criação do certificado e ciclo de vida do laboratório:

```bash
scripts/create_gateway_lab_certificate.sh sister-gateway.test
scripts/run_gateway_lab.sh
scripts/stop_gateway_lab.sh
```

O certificado é assinado por uma CA efêmera local. Os testes usam
`.run/gateway/ca-lab.crt` para validar a cadeia e o SAN; `curl -k` não faz
parte dos critérios de aceitação. O processo escuta somente em loopback.

O laboratório não está promovido: HAProxy 3.2.22 normalizou duplicações
idênticas e alguns campos hop-by-hop antes das ACLs. Esses resultados são
`PARTIALLY_PROVEN` e mantêm SEC-03B aberto.

O binário deve pertencer à linha 3.2 e ser 3.2.22 ou posterior. O renderizador
recusa caminhos relativos, permissões excessivas, interface pública, porta 443
no laboratório, wildcard de Host, upstream alternativo e placeholders
residuais. A validação offline usa `haproxy -c -V` e não inicia processo.
