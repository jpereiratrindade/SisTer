# SEC-03B — gateway mínimo em laboratório

**Data:** 2026-08-01

**Branch:** `sec-03b-lab`

**Estado:** `LAB_PROVEN_WITH_RESTRICTIONS`

**Exposição externa:** não autorizada

## Ambiente observado

O laboratório executou HAProxy Community 3.2.22 a partir da imagem oficial
`docker.io/library/haproxy:3.2.22`, digest
`sha256:fc0fd23c2d99d93cc0370b43bd52432cf9c078e29590e8d73448a38ad10e03b4`.
O listener permaneceu em `127.0.0.1:8443`, com upstream literal
`127.0.0.1:8000`. Certificados, configuração renderizada, PID e logs ficaram
sob `.run/gateway/` e não são versionados.

O certificado foi assinado por CA efêmera, contém SAN
`sister-gateway.test` e foi validado pelo cliente sem `curl -k`. O PEM combinado
ficou em modo `0600`; a configuração, em `0640`.

## Evidência executada

```text
renderizador e mutações negativas                 PASS
haproxy -c -V                                     PASS
gateway_protocol_test.py                          PASS
gateway_header_sanitization_test.py               PASS
gateway_failure_test.py                           PASS
gateway_lab_test.py → sisterd real                PASS
curl com CA/SAN → gateway → /api/health real      PASS
```

O pipeline geral permanece independente da instalação local do HAProxy: os
quatro testes dinâmicos usam `GATEWAY_HAPROXY_BIN` quando fornecido e retornam
`SKIP` explícito quando o laboratório não está instalado. Nesta evidência, eles
foram executados com o binário 3.2.22 acima e não foram pulados.

## Matriz de resultado

| Requisito | Estado | Resultado observado |
|---|---|---|
| configuração governada e upstream fixo | `PROVEN` | renderizador recusou interface, porta, Host, PEM e upstream inseguros; `haproxy -c` aprovou a saída |
| TLS 1.3 | `PROVEN` | conexão validada por CA e SAN |
| TLS 1.2 | `PROVEN` | handshake recusado |
| HTTP/1.1 por ALPN | `PROVEN` | `http/1.1` negociado; cliente apenas `h2` não negociou protocolo |
| HTTP sem TLS em 8443 | `PROVEN` | nenhuma resposta HTTP em claro |
| SNI e Host canônicos | `PROVEN` | SNI divergente recusado; Host canônico sem porta ou com `8443` aceito |
| Host ausente, desconhecido, wildcard ou porta inesperada | `PROVEN` | requisições recusadas antes do upstream |
| duas linhas Host idênticas | `ACCEPTED_LAB_DIVERGENCE` | HAProxy 3.2.22 normalizou as ocorrências; um único Host canônico chegou ao upstream sob a exceção restrita SEC-03B-R |
| duas linhas Host divergentes | `PROVEN` | ambas as ordens receberam `400` e não alcançaram o upstream |
| absolute-form | `PROVEN` | recusado com `400`, independentemente da combinação com Host |
| métodos permitidos | `PROVEN` | método fora da allowlist recebeu `405` |
| corpo geral e autenticação | `PROVEN` | limites exatos foram aceitos; limite mais um byte recebeu `413` |
| mais de 64 unidades de header | `PROVEN` | requisição com 70 headers adicionais recebeu `400` |
| `Transfer-Encoding` | `PROVEN` | requisição chunked recebeu `400` |
| duas linhas Content-Length idênticas | `PROVEN_BY_SAFE_NORMALIZATION` | duas linhas válidas com valor `5` produziram um único `Content-Length: 5` e corpo íntegro no upstream |
| Content-Length inválido ou divergente | `PROVEN` | valores divergentes receberam `400` e não alcançaram o upstream |
| headers `X-Sister-*` | `PROVEN` | ausentes no upstream de captura |
| origem e correlação externas | `PROVEN` | `Forwarded` removido; `X-Forwarded-*` reconstruídos; ID externo substituído por 32 hex minúsculos |
| cookie na fronteira gateway/sisterd | `PROVEN` | preservado até o `sisterd`; nenhum endpoint de depuração foi criado |
| handshake WebSocket completo | `PROVEN_BY_REJECTION` | `Upgrade: websocket` com `Connection: Upgrade` recebeu `400` e não chegou ao upstream |
| headers de Upgrade isolados | `PROVEN_BY_STRIPPING` | HAProxy retirou `Upgrade` e `Connection`; a requisição seguiu apenas como HTTP comum |
| sisterd indisponível | `PROVEN` | gateway retornou `503` controlado |
| PEM ausente ou permissivo | `PROVEN` | renderizador bloqueou o início |
| sisterd real e quarentena funcional | `PROVEN` | `/api/health` passou; Clima permaneceu `404`; Nexo sem identidade não ganhou acesso |
| gateway → sisterd → Nexo → PostgreSQL | `DEFERRED_TO_SEC-03V` | composição permanece obrigatória com identidade efêmera e ambiente integrado governado |

## Controles deliberadamente não verdes

| Controle | Estado após o laboratório |
|---|---|
| taxa mínima sustentada de 1 KiB/s | `UNPROVEN` |
| resposta upstream máxima de 16 MiB | `UNPROVEN` |
| rate limiting multidimensional completo | `SEC-03C_PENDING` |
| 32 conexões efetivas por origem | `SEC-03C_PENDING` |
| isolamento local por usuário/cgroup | `NOT_IMPLEMENTED` |
| confiança do sisterd em headers do gateway | `DISABLED` |

## Resolução SEC-03B-R

SEC-03B está encerrado como `LAB_PROVEN_WITH_RESTRICTIONS`. A decisão adota a
regra de enquadramento do [RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html):
valores `Content-Length` válidos e idênticos podem ser reduzidos a um valor
efetivo; valores inválidos ou divergentes permanecem erro irrecuperável. Campos
isolados de Upgrade são neutralizados por remoção, enquanto o handshake completo
é rejeitado.

A duplicação idêntica de `Host` permanece `ACCEPTED_LAB_DIVERGENCE`, pois o RFC
9112 exige rejeitar mais de uma linha Host e o HAProxy a normaliza antes das
ACLs. O owner é **gateway and transport maintainers**. A aceitação vale somente
com um SNI/certificado, um Host exato, um upstream literal e reconstrução do Host
canônico. Múltiplos hosts, certificados, backends, destino dinâmico ou troca da
linha/representação HTTP reabrem o gate. SEC-03V deve reavaliar o risco.

Esta resolução autoriza iniciar SEC-03C. Não autoriza merge em `main`, release,
tag ou exposição externa. O E2E completo com Nexo foi transferido, não removido,
para SEC-03V.

A tag `v0.2.7` e `VERSION` permanecem imutáveis. Nenhum listener público,
certificado institucional, WebSocket, Clima ou confiança em headers foi
habilitado.
