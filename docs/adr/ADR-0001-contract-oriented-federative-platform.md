# ADR-0001: Plataforma federativa orientada por contratos

## Status

Aceita

## Contexto

O SisTer deve articular sistemas territoriais autonomos sem exigir que todos sejam reescritos como aplicacoes de um framework central.

## Decisao

O SisTer nasce como plataforma federativa orientada por contratos. O repositorio prioriza `contracts/`, `core/`, evidencias, proveniencia e governanca antes de uma aplicacao web completa.

## Consequencias

- Sistemas federados mantem autonomia operacional.
- A integracao depende de manifestos, CampoSync, schema validation e proveniencia.
- C++20 sera a base inicial do nucleo pela combinacao de portabilidade, maturidade de toolchain e capacidade de rodar em ambiente local/offline.
- Servidor HTTP, SQLite e PWA ficam como proximos incrementos, nao como premissas do primeiro teste.
