# SEC-03C — contenção de abuso e recursos no gateway

**Data:** 2026-08-02

**Branch:** `sec-03c-lab`

**Estado:** `LAB_PROVEN_WITH_RESTRICTIONS`

**Exposição, merge e release:** não autorizados

## Ambiente e configuração observados

O laboratório manteve HAProxy Community 3.2.22, TLS somente em
`127.0.0.1:8443` e um único upstream literal em `127.0.0.1:8000`. A
configuração passou em `haproxy -c -V`; Lua, plugins, destinos dinâmicos,
WebSocket e portas públicas permaneceram ausentes.

O perfil executável `sister.gateway-security-profile/1.2.0` fixa:

| Recurso | Limite |
|---|---:|
| conexões globais | 1024 |
| conexões por origem | 32 |
| conexões simultâneas ao upstream | 32 |
| fila por servidor | 64 por até 2 s |
| requisições globais | 1000/10 s |
| requisições por origem | 120/60 s |
| requisições por origem e rota | 60/60 s |
| login por origem | 10/60 s |

## Evidência executada

```text
validate_gateway_security_profile.py                 PASS
gateway_security_profile_test.py                     PASS
gateway_config_render_test.py                        PASS
haproxy -c -V                                        PASS
gateway_protocol_test.py                             PASS
gateway_header_sanitization_test.py                  PASS
gateway_failure_test.py                              PASS
gateway_abuse_test.py                                PASS
gateway_slow_client_test.py                          PASS
gateway_upstream_resilience_test.py                  PASS
```

## Ameaça → controle → teste → resultado → risco residual

### Abuso de requisições

**Ameaça:** uma origem, rota ou endpoint de autenticação consumir capacidade
ou contornar o limite abrindo nova porta de origem.

**Mecanismo:** quatro stick tables independentes e cinco stick counters. O
login exato `/api/auth/login` é avaliado primeiro e possui o menor limite.

**Teste e resultado:** rajadas abaixo do limite chegaram ao upstream; a
primeira requisição excedente recebeu `429` com `Retry-After`, sem novo registro
no upstream. Novas conexões TCP da mesma origem preservaram o contador. Rotas e
origens distintas permaneceram independentes. Estado: `PROVEN`.

**Risco residual:** os valores são baseline de laboratório, ainda sem
calibração de carga institucional; o limitador interno do `sisterd` permanece
como defesa em profundidade.

### Conexões e fila

**Ameaça:** uma origem ou um upstream lento esgotar conexões e impedir serviço
para terceiros.

**Mecanismo:** `maxconn` global, `conn_cur` por origem, `maxconn 32` e
`maxqueue 64` no único servidor, `timeout queue 2s` e `abortonclose`.

**Teste e resultado:** 32 conexões simultâneas de uma origem foram mantidas e a
33ª recusada; outra origem continuou obtendo `200`. Sob 100 requisições retidas,
houve respostas normais e falhas `503` controladas, seguidas por health `200`.
Estado: `PROVEN`.

**Risco residual:** o limite global de 1024 foi validado estruturalmente, não
por saturação completa neste host; desempenho e justiça sob carga real ficam
para SEC-03V.

### Clientes lentos

**Ameaça:** handshake, headers, corpo parcial ou keep-alive reterem recursos
indefinidamente.

**Mecanismo:** handshake TLS e headers em 5 s, keep-alive em 2 s e inatividade
do cliente em 15 s.

**Teste e resultado:** conexão sem handshake, headers incompletos, corpo
interrompido e keep-alive ocioso foram encerrados dentro dos limites observados;
o health permaneceu funcional. Estado: `PARTIALLY_PROVEN`.

**Risco residual:** o timeout do corpo após os headers é de inatividade, não um
deadline absoluto para todo corpo, e não prova taxa mínima de 1 KiB/s. Ambos não
podem ser promovidos para garantia exata por este laboratório.

### Upstream indisponível, lento e recuperado

**Ameaça:** falha ou lentidão do `sisterd` propagar retenção ou resposta
indeterminada.

**Mecanismo:** health check, connect/queue/response timeouts, fila limitada e
erros JSON sanitizados `503`/`504`.

**Teste e resultado:** upstream parado produziu `503`; upstream que não
respondeu produziu `504`; saturação falhou de forma controlada; o retorno do
upstream restaurou `200` sem reiniciar o gateway. Estado: `PROVEN`.

**Risco residual:** alta disponibilidade e limite de resposta de 16 MiB estão
fora deste gate; o segundo permanece `UNPROVEN`.

### Memória dos limitadores

**Ameaça:** cardinalidade de origens ou rotas fazer o processo crescer sem
limite.

**Mecanismo:** capacidades de 1, 128 ou 512 entradas, expiração de 10 a 60 s e
política padrão de expulsão das entradas mais antigas, sem `nopurge`. Um socket
runtime modo `0600` expõe ocupação somente ao operador do laboratório.

**Teste e resultado:** 1000 origens simuladas não fizeram a tabela de origem
ultrapassar 128 entradas; `show table` confirmou capacidade e uso. Estado:
`PROVEN`.

**Risco residual:** churn distribuído pode expulsar histórico e reduzir a
eficácia por origem; a contenção global permanece ativa e SEC-03V deve calibrar
capacidade e memória.

### Observabilidade sem segredos

**Ameaça:** bloqueios não diagnosticáveis ou vazamento de credenciais nos logs.

**Mecanismo:** uma linha JSON por requisição com ID gerado, origem, rota sem
query, status, tempos total/fila/upstream, regra e resultado do limitador.

**Teste e resultado:** um bloqueio de login foi correlacionado por ID e regra;
Authorization, Cookie, asserção, query e senha injetados não apareceram no log.
Estado: `PROVEN` no laboratório.

**Risco residual:** retenção, exportação, integridade e correlação completa com
`sisterd`, Nexo e PostgreSQL pertencem a SEC-03V.

## Regressões de SEC-03B

TLS 1.3, SNI/Host canônicos, enquadramento HTTP, saneamento de headers,
bloqueio de WebSocket e upstream literal foram reexecutados. A duplicação
idêntica de Host continua `ACCEPTED_LAB_DIVERGENCE` sob o mesmo escopo; nenhuma
asserção Nexo é emitida fora da rota aprovada pelo `sisterd`.

## Decisão e caminho crítico

SEC-03C encerra como `LAB_PROVEN_WITH_RESTRICTIONS`. Isso autoriza iniciar
`ISO-01`, não autoriza merge em `main`, alteração de `VERSION`, tag, release ou
exposição externa.

```text
SEC-03C → ISO-01 → SEC-03V → merge controlado → v0.2.8
```

Permanecem `UNPROVEN` a taxa mínima exata de 1 KiB/s e o limite exato de
resposta upstream de 16 MiB. O acesso local ao `sisterd` por outros processos
continua `NOT_IMPLEMENTED` até ISO-01.
