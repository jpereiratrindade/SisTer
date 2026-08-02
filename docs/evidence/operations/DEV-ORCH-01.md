# DEV-ORCH-01 — classificação composta do ambiente local

**Data:** 2026-08-02

**Estado:** `PROVEN_IN_DEVELOPMENT`

## Achado

A execução comum aprovou qualidade, `sisterd` e smoke, mas encontrou Nexo e
Studio indisponíveis. A mensagem final apresentava sucesso integral mesmo com
degradação opcional. Não houve falha em ISO-01 ou no núcleo do SisTer.

## Contrato implementado

| Perfil | Núcleo | Gateway dinâmico | Subsistemas | Política |
|---|---|---|---|---|
| `dev-core` | obrigatório | opcional | não consultados | `PASS` |
| `dev-ecosystem` | obrigatório | opcional | todos opcionais | permite `PASS_WITH_DEGRADATION` |
| `test-core` | obrigatório | opcional | não consultados | `PASS` |
| `sec-03v` | obrigatório | obrigatório | somente Nexo, obrigatório | falha produz `BLOCKED`; não fecha o gate |

O agregador não atualiza repositórios nem reconcilia serviços saudáveis por
mudança de fontes sem `--update-subsystems`. Cada componente continua dono de
seu runner, diagnóstico e reparo.

## Causas observadas, sem reparo cruzado

- Nexo: o runner construiu `sister-nexo` e `nexo_core_tests`, mas o CTest também
  esperava `nexo_internal_identity_tests`, que não estava no conjunto criado;
- Studio: o runner encontrou um `CMakeCache.txt` gerado sob outro caminho de
  workspace.

Esses diagnósticos pertencem aos repositórios correspondentes. O SisTer apenas
registra fase, código de saída e caminho do log.

## Reprodução

```text
run_all.sh --profile dev-core
  core quality          PASS
  sisterd readiness     READY
  smoke                 PASS
  subsystems            NOT_REQUESTED
  overall               PASS
  exit                  0

run_all.sh --profile dev-ecosystem
  core quality          PASS
  sisterd readiness     READY
  smoke                 PASS
  sister_nexo           DEGRADED/startup/exit 1
  sister_clima          READY
  sister_studio         DEGRADED/startup/exit 1
  sister_compras        READY
  overall               PASS_WITH_DEGRADATION
  exit                  0

run_all.sh --profile sec-03v, sem GATEWAY_HAPROXY_BIN
  prerequisite          BLOCKED
  exit                  2
```

A primeira tentativa de `dev-core` também revelou uma instância TCP de uma
execução anterior durante o teste Unix. O agregador agora encerra sua instância
`sisterd` anterior antes da qualidade; o teste de ausência de TCP permaneceu
inalterado e passou na reprodução final.

## Códigos

```text
0  PASS ou PASS_WITH_DEGRADATION em perfil permissivo
1  falha na qualidade/prontidão do núcleo
2  componente obrigatório ou pré-requisito bloqueado
3  erro de configuração/orquestração
```
