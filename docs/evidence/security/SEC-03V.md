# SEC-03V — validação integral da fronteira HTTP

**Data:** 2026-08-02  
**Host:** Fedora 44 Workstation  
**Estado:** `PASS`  
**Escopo:** laboratório candidato privilegiado, sem exposição pública

## Baseline

```text
SisTer   dad87e3994840b28ee217760a6569c7f75400440
Nexo     f77196ed8dbd30fc009066a73086972dcd4c437c
HAProxy  sister-haproxy-lab-3.2.22-1.sistersec03v.fc44.x86_64
```

O HAProxy foi instalado pelo RPM assinado do laboratório, com fingerprint
`ED3F4CE4C756983F211097B6AB5D893C71F31D65`, e permaneceu sem divergências em
`rpm -V`. O serviço candidato executou o binário nativo
`/usr/local/sbin/haproxy-3.2.22` sob `sister-gateway`.

## Preflight do ambiente

```text
schema   sister.sec03v-env-preflight/1.0.0
result   READY
checks   42
PASS     42
BLOCKED  0
SHA-256  b1206a16475c0fd3c5c6f3cb4ddd8b9dfcbb7e3e77806ccb03c854db02ae6d20
```

O relatório preservado em
`/var/lib/sister-sec03v-env/sec03v-env-preflight-sec03v.json` foi copiado para
`.run/security/sec03v-env-preflight-sec03v.json` para revisão. A evidência
detalhada do ambiente está em [SEC-03V-ENV.md](./SEC-03V-ENV.md).

## Execução sem skips

Com o gateway candidato e o binário RPM nativo:

```text
gateway_protocol_test              PASS
gateway_header_sanitization_test   PASS
gateway_failure_test                PASS
gateway_abuse_test                  PASS
gateway_slow_client_test           PASS
gateway_upstream_resilience_test   PASS
gateway_lab_test                    PASS
-----------------------------------------
7/7 PASS   0 SKIP   0 FAIL
```

Os testes foram executados com `ctest` usando
`GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22`. Após a execução, os
artefatos de laboratório foram restaurados e o serviço candidato foi
reativado.

## Observações de runtime

- `sisterd.socket`, `sisterd.service` e `sister-gateway.service`: `active`;
- socket de controle: `/run/sister/sisterd.sock`, `sister:haproxy`, `0660`;
- listener do gateway: somente `127.0.0.1:8443`;
- listener TCP produtivo do `sisterd` em `:8000`: ausente;
- health TLS 1.3: `200`;
- resposta observada: `service=sisterd`, `database=connected`;
- Nexo e PostgreSQL: `READY`, com identidade assinada `kid=identity-2026-08`.

## Decisão

O gate `SEC-03V` está **PASS** no ambiente candidato delimitado. A evidência
comprova a fronteira HTTP, o transporte Unix, as identidades de serviço, a
proveniência do gateway, a prontidão do Nexo e a matriz dinâmica sem skips.

Esta decisão não autoriza, por si só, exposição externa, alteração de tags ou
publicação de release. Merge coordenado em `main`, atualização do MAES como
baseline aprovada e criação da `v0.2.8` permanecem ações posteriores, sujeitas
a revisão do diff e decisão explícita de promoção.

## Riscos residuais

O resultado é limitado ao host e aos artefatos registrados acima. Não cobre
alta disponibilidade, operação multi-host, carga institucional ou compromisso
do próprio host/root. O listener continua restrito a loopback e o certificado
é exclusivo do laboratório.
