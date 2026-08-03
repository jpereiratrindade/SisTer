# WP-FED-01 — Registro governado de sistemas e capacidades

## Objetivo

Materializar a identidade federativa necessária para associar futuros acordos e
execuções a participantes e capacidades reais.

## Estado

Registro em memória e modelo de domínio inicial. Classificação MVP-01:
`TESTADO_EM_MEMORIA`. Não está `PERSISTIDO`, `OPERÁVEL` ou `GOVERNADO`.

## Entregas atuais

- identificadores fortes para sistema, versão, capacidade e owner;
- `CapabilityDeclaration` versionada e ligada a contrato;
- estados operacionais independentes de maturidade;
- registro governado em memória;
- rejeição de duplicidade e declarações sem contrato;
- testes de registro e descoberta.
- contrato `federated-system-manifest/1.0.0` e validador reproduzível;
- registro idempotente para manifesto idêntico;
- conflito e capacidades duplicadas rejeitados;
- atualização de estado operacional e maturidade por operações explícitas.

## Fora de escopo

Acordos, execuções, persistência definitiva, HTTP, Nexo–Compras e
`AssessmentEngine`.

## Gate

O gate fecha quando identidade, versões, capacidades, estados independentes,
duplicidades e contratos forem validados por testes e exemplos de contrato.

Evidência:

```text
./scripts/contracts/validate-federation.sh
```
