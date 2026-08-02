# SEC-03B — gateway mínimo em laboratório

**Data:** 2026-08-01

**Branch:** `sec-03b-lab`

**Estado:** `LAB_INCOMPLETE`
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
| Host canônico, ausente, desconhecido e wildcard | `PROVEN` | `200`, `400`, `403` e `403`, respectivamente |
| duas linhas Host idênticas | `PARTIALLY_PROVEN` | HAProxy 3.2.22 normalizou as ocorrências antes da ACL e encaminhou a requisição; requisito de rejeição não foi satisfeito |
| métodos permitidos | `PROVEN` | método fora da allowlist recebeu `405` |
| corpo geral e autenticação | `PROVEN` | limites exatos foram aceitos; limite mais um byte recebeu `413` |
| mais de 64 unidades de header | `PROVEN` | requisição com 70 headers adicionais recebeu `400` |
| `Transfer-Encoding` | `PROVEN` | requisição chunked recebeu `400` |
| duas linhas Content-Length idênticas | `PARTIALLY_PROVEN` | o parser normalizou valores idênticos antes da ACL e encaminhou a requisição; valores conflitantes continuam fechados pelo parser, mas a política exige rejeitar toda duplicação |
| headers `X-Sister-*` | `PROVEN` | ausentes no upstream de captura |
| origem e correlação externas | `PROVEN` | `Forwarded` removido; `X-Forwarded-*` reconstruídos; ID externo substituído por 32 hex minúsculos |
| cookie na fronteira gateway/sisterd | `PROVEN` | preservado até o `sisterd`; nenhum endpoint de depuração foi criado |
| handshake WebSocket completo | `PROVEN` | `Upgrade: websocket` com `Connection: Upgrade` recebeu `400` e não chegou ao upstream |
| headers de Upgrade isolados | `PARTIALLY_PROVEN` | HAProxy retirou os campos hop-by-hop e encaminhou sem handshake; o upstream não recebeu Upgrade, mas o status explícito de rejeição não foi produzido |
| sisterd indisponível | `PROVEN` | gateway retornou `503` controlado |
| PEM ausente ou permissivo | `PROVEN` | renderizador bloqueou o início |
| sisterd real e quarentena funcional | `PROVEN` | `/api/health` passou; Clima permaneceu `404`; Nexo sem identidade não ganhou acesso |
| gateway → sisterd → Nexo → PostgreSQL | `BLOCKED` | não havia configuração de identidade privada e sessão de teste aprovada para executar o E2E sem alterar credenciais ou dados operacionais |

## Controles deliberadamente não verdes

| Controle | Estado após o laboratório |
|---|---|
| taxa mínima sustentada de 1 KiB/s | `UNPROVEN` |
| resposta upstream máxima de 16 MiB | `UNPROVEN` |
| rate limiting multidimensional completo | `SEC-03C_PENDING` |
| 32 conexões efetivas por origem | `SEC-03C_PENDING` |
| isolamento local por usuário/cgroup | `NOT_IMPLEMENTED` |
| confiança do sisterd em headers do gateway | `DISABLED` |

## Decisão

SEC-03B não está encerrado. O laboratório prova a maior parte da fronteira
mínima, mas não permite classificar como `PROVEN` a rejeição de ocorrências
idênticas de `Host` e `Content-Length`, nem o status de bloqueio para campos de
Upgrade isolados. Não será introduzido Lua, plugin ou módulo para esconder essas
lacunas. Antes de SEC-03C, a equipe deve decidir por um mecanismo nativo simples,
reformular a política com justificativa de normalização ou manter o gate
bloqueado.

A tag `v0.2.7` e `VERSION` permanecem imutáveis. Nenhum listener público,
certificado institucional, WebSocket, Clima ou confiança em headers foi
habilitado.
