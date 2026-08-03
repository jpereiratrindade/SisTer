# Subsistema de Referência SisTer

## Propósito

Implementação mínima controlada para provar funções do SisTer sem depender de
comportamento específico de produtos externos.

## Contrato mínimo

- identidade e manifesto `sister.subsystem/1.0.0`;
- health e readiness;
- capacidades `reference.identity.read` e `reference.echo.execute`;
- `GET /api/whoami` para identidade mediada;
- `POST /api/echo` para percurso funcional completo;
- loopback `127.0.0.1:19001`, sem banco, TLS interno ou frontend.

## Modos parametrizados

`SISTER_REFERENCE_MODE` aceita `healthy`, `degraded`, `unavailable`, `delayed`,
`invalid-response`, `http-401`, `http-403`, `http-404`, `http-500` e
`connection-closed`. Latência e taxa de falha usam
`SISTER_REFERENCE_DELAY_MS` e `SISTER_REFERENCE_FAILURE_RATE`.

## Funções verificadas

Descoberta, contrato, início, prontidão, autenticação, reconstrução de
identidade, encaminhamento, timeout, erro sanitizado, parada, queda e
preservação do núcleo.

## Conformidade externa

A referência é normativa, não exemplo adaptável. Integração real deve provar
compatibilidade com suas fronteiras antes de voltar aos perfis oficiais.
