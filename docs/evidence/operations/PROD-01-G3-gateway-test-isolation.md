# PROD-01-G3 — Isolamento entre Gateway Operacional e Testes

Gate: PROD-01-G3
Área: Operação
Status: PASS
Data: 2026-08-03
Ambiente: teste de produção LAN

## Contexto

Durante o teste de produção, rotas que deveriam chegar ao núcleo passaram a
retornar:

```text
{"error":"service_unavailable"}
```

O gateway continuava entregando a página principal, mas `/admin/maturity` e
`/integrations/clima` retornavam erro de indisponibilidade. Os logs do HAProxy
mostraram que o backend `sisterd_internal` estava sem servidor disponível por
ausência do socket Unix:

```text
Server sisterd_internal/sisterd is DOWN
Socket error: No such file or directory
backend 'sisterd_internal' has no server available
```

## Causa

A suíte dinâmica do gateway usava o mesmo runtime root do gateway LAN:

```text
.run/gateway/sisterd.sock
```

Alguns testes removiam esse socket para simular indisponibilidade de upstream.
Quando executados com o gateway LAN ativo, os testes apagavam o socket
operacional e o HAProxy passava a responder `503 service_unavailable`.

## Correção

Os testes dinâmicos do gateway passaram a usar runtime root próprio:

```text
.run/gateway-tests/<pid>
```

Os scripts de gateway agora aceitam `GATEWAY_RUN_ROOT` para isolar certificados,
configuração, stats socket e upstream socket de laboratório, mantendo
`.run/gateway` como padrão operacional LAN.

Arquivos alterados:

- `tests/gateway_lab_support.py`
- `scripts/render_gateway_config.py`
- `scripts/create_gateway_lab_certificate.sh`
- `scripts/validate_gateway_config.sh`

## Critérios Verificados

- a suíte dinâmica não altera `.run/gateway/sisterd.sock`;
- o backend operacional permanece disponível após os testes;
- `/api/health` continua respondendo HTTP `200`;
- `/admin/maturity` alcança o `sisterd` e retorna `401` sem sessão;
- `/integrations/clima` retorna `404` quando o acesso operacional não está
  publicado;
- `503` volta a representar falha real do gateway/backend, não colisão com a
  suíte.

## Validação Executada

```bash
cmake --build build --target sisterd --parallel
python3 tests/gateway_config_render_test.py
python3 tests/sisterd_maturity_api_test.py build/apps/sisterd/sisterd web .
python3 tests/sisterd_nexo_identity_test.py build/apps/sisterd/sisterd web
GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22 \
  python3 tests/gateway_lab_test.py build/apps/sisterd/sisterd web
GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22 \
  python3 tests/gateway_upstream_resilience_test.py
python3 scripts/validate_governance_repo.py
./scripts/validate_shell_scripts.sh
```

Verificação operacional após reinício do gateway LAN:

```text
/api/health         -> 200
/admin/maturity     -> 401
/integrations/clima -> 404
```

Resultado: PASS.
