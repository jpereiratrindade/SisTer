# ISO-01 — isolamento local do upstream

**Data:** 2026-08-02

**Branch:** `iso-01-lab`

**Estado:** `LAB_PROVEN_WITH_RESTRICTIONS`

**Próximo gate:** `SEC-03V`

**Merge, release, tag e exposição externa:** não autorizados

## Escopo observado

O transporte produtivo de entrada foi alterado de TCP loopback para o socket
Unix ativado `/run/sister/sisterd.sock`. O transporte de saída do `sisterd`
para Nexo/PostgreSQL e a política de confiança em `X-Forwarded-*` e
`X-Request-ID` não foram alterados.

O laboratório usa um caminho efêmero sob `.run/` com a mesma validação de
descritor. O caminho produtivo permanece fixo e não pode ser substituído por
configuração de ambiente.

## Evidência executada

```text
build C++20 com -Wall -Wextra -Wpedantic                 PASS
sisterd_unix_listener_test.py                            PASS
sisterd_transport_quarantine_test.py                     PASS
sisterd_systemd_unit_test.py                             PASS
gateway_config_render_test.py                            PASS
gateway_protocol/header/failure tests sobre AF_UNIX      PASS
gateway_lab_test.py → HAProxy real → sisterd real         PASS
pipeline integral                                        PASS
git diff --check                                          PASS
```

## Matriz de controle

| Controle | Estado | Resultado e risco residual |
|---|---|---|
| ausência do listener TCP | `PROVEN` | processo ativado respondeu pelo Unix socket e `127.0.0.1:8000` recusou conexão |
| socket Unix exclusivo | `PROVEN` | exatamente um descritor, `AF_UNIX`, `SOCK_STREAM`, `SO_ACCEPTCONN`, nome e caminho exatos |
| HAProxy autorizado | `PROVEN` | HAProxy 3.2.22 alcançou o `sisterd` real por `unix@...` e recebeu health `200` |
| usuário comum bloqueado | `PARTIALLY_PROVEN` | modo sem permissão produziu `EACCES`; contas reais `sister`/`haproxy` não existem no host do laboratório |
| ausência de fallback | `PROVEN` | socket ausente ou inválido encerrou o processo; tentativa explícita de fallback foi recusada; nenhuma porta apareceu |
| reinício seguro | `PROVEN` | segundo processo recebeu o mesmo descritor; inode e modo permaneceram estáveis |
| rollback sem exposição | `PARTIALLY_PROVEN` | artefatos e proibições estão versionados; instalação/rollback real sob PID 1 não foi executado |
| integração Nexo preservada | `DEFERRED_TO_SEC-03V` | emissão assinada e E2E PostgreSQL continuam no gate integral |
| SELinux específico | `DEFERRED` | nenhum bloqueio surgiu no laboratório; política do host candidato ainda não foi exercitada |

## Falhas fechadas comprovadas

```text
zero descritores                 → arranque recusado
mais de um descritor             → arranque recusado
descritor fechado                → arranque recusado
descritor sem listen             → arranque recusado
família/tipo incorreto           → arranque recusado
nome do descritor incorreto      → arranque recusado
nome do descritor ausente        → arranque recusado
caminho diferente                → arranque recusado
modo TCP em produção             → configuração recusada
host/porta TCP em produção       → configuração recusada
fallback TCP                     → configuração recusada
arquivo comum no caminho         → não substituído
symlink no caminho               → não seguido nem substituído
```

O `sisterd` não cria, remove ou corrige o socket produtivo. Essa responsabilidade
permanece no `systemd`; assim, um erro de provisionamento não é mascarado por
`bind()` ou fallback executado pela aplicação.

## Permissões e ciclo de vida definidos

```text
/run/sister
  root:haproxy 0750

/run/sister/sisterd.sock
  sister:haproxy 0660
  Accept=no
  RemoveOnStop=yes
  FileDescriptorName=sisterd-http
```

`ops/tmpfiles.d/sister.conf`, `sisterd.socket` e `sisterd.service` são validados
como conjunto. A implantação deve ainda confirmar no host candidato:

- existência e natureza não interativa das contas;
- ausência de usuários comuns no grupo `haproxy`;
- owner/grupo/modo efetivos após boot e restart;
- remoção efetiva ao parar `sisterd.socket`;
- comportamento da política SELinux ativa.

A garantia comprovada é que processos locais comuns sem a identidade ou o
grupo autorizados são impedidos pelo kernel de conectar ao socket produtivo.
`root`, comprometimento da identidade/grupo autorizado, alteração privilegiada
das unidades e comprometimento do host permanecem riscos residuais.

## Regressões preservadas

- SEC-03B: TLS, autoridade canônica, framing e bloqueio de WebSocket continuam;
- SEC-03C: limites, fila, timeouts, erros controlados e logs continuam;
- SEC-02M: `sisterd` não passou a confiar em headers do gateway e somente a rota
  assinada exata continua elegível;
- desenvolvimento/teste conserva TCP loopback explícito, sem alterar produção.

## Decisão

ISO-01 encerra em laboratório como `LAB_PROVEN_WITH_RESTRICTIONS`. A brecha
estrutural do listener TCP produtivo foi removida, mas a prova de identidades
reais e do ciclo completo do systemd é obrigatória no ambiente candidato.

```text
ISO-01 → SEC-03V → revisão/merge controlado → v0.2.8
```
