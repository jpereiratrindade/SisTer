# HAProxy de laboratório — SEC-03B/03C/ISO-01

Este diretório contém somente fontes versionadas. Configuração renderizada,
certificados, chaves, PID e logs pertencem a `.run/gateway/`, que é ignorado
pelo Git.

O template materializa a fronteira validada nos laboratórios SEC-03B/03C/ISO-01:

- listener `127.0.0.1:8443`, TLS 1.3 e HTTP/1.1;
- SNI estrito, Host/porta exatos, absolute-form recusado e métodos em allowlist;
- destino Unix literal sob `.run/gateway/sisterd.sock` no laboratório e
  `/run/sister/sisterd.sock` em produção;
- regras de rejeição para `Transfer-Encoding`, `Content-Length` duplicado,
  Upgrade e WebSocket, sujeitas aos resultados de normalização documentados em
  `docs/evidence/security/SEC-03B.md`;
- limites declarados de corpo;
- remoção dos headers externos governados e criação de novo request ID;
- health check do `sisterd`.
- limites independentes global, por origem, rota e login;
- conexões, concorrência upstream, fila e stick tables limitadas;
- falhas JSON controladas e log estruturado sem query ou segredos.

Não contém confiança do `sisterd` nos headers, limite de resposta ou taxa
mínima. A separação real de usuários/grupos permanece para o host candidato.
Lua, plugins, resolvers,
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

Para testar a fronteira pela rede local, use o perfil separado `lan-lab`.
Ele aceita somente um IPv4 privado explícito, mantém o `sisterd` no socket Unix
e não abre as portas TCP 8000 ou 8001. O candidato de produção continua em
loopback conforme SEC-03V.

```bash
export GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22
export GATEWAY_LAN_ADDRESS=10.163.80.176
./scripts/run_gateway_lan_lab.sh
```

O ciclo termina com:

```bash
./scripts/stop_gateway_lan_lab.sh
```

O script mostra o caminho da CA em `.run/gateway/ca-lab.crt`. Em cada cliente
da rede, resolva o Host exato `sister-gateway.test` para o IP do laptop e
instale essa CA como autoridade de teste. Libere TCP 8443 somente na rede de
teste, se o firewall do laptop bloquear a interface. O endereço final é
`https://sister-gateway.test:8443`.

O login do `lan-lab` usa PostgreSQL diretamente por
`SISTER_AUTH_BACKEND=postgresql`; o bootstrap HTTP fica desativado. Antes do
primeiro início, crie a conta persistente pelo terminal:

```bash
./scripts/bootstrap_gateway_lan_admin.sh \
  "Administrador LAN" admin@example.org
./scripts/run_gateway_lan_lab.sh
```

SEC-03B está encerrado como `LAB_PROVEN_WITH_RESTRICTIONS`: `Content-Length`
idêntico é normalizado com segurança, campos Upgrade isolados são removidos e
Host idêntico duplicado permanece `ACCEPTED_LAB_DIVERGENCE` sob autoridade
canônica única. Isso autoriza SEC-03C, não implantação ou exposição.

SEC-03C também está encerrado como `LAB_PROVEN_WITH_RESTRICTIONS`. Sua evidência
autoriza iniciar ISO-01, mas não merge, implantação, release, tag ou exposição.

ISO-01 está encerrado com restrições e autoriza iniciar somente SEC-03V. O
backend TCP foi removido; o laboratório usa AF_UNIX e produção exige socket
activation no caminho canônico.

O binário deve pertencer à linha 3.2 e ser 3.2.22 ou posterior. O renderizador
recusa caminhos relativos, permissões excessivas, interface pública, porta 443
no laboratório, wildcard de Host, upstream alternativo e placeholders
residuais. A validação offline usa `haproxy -c -V` e não inicia processo.
