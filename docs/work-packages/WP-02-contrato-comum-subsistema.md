# WP-02: Contrato comum de subsistema

## Status

Proposto para abertura da fase Alfa.

## Objetivo arquitetural

Publicar `sister.subsystem/1.0.0` como contrato comum para integração de
subsistemas ao SisTer, substituindo integrações específicas por uma fronteira
versionada, validável e aplicável a Clima, Nexo e subsistemas futuros.

Este pacote inaugura a fase Alfa porque define a fronteira sobre a qual serão
construídos capacidades, identidade interna assinada, adaptadores, registry e
testes de conformidade.

## Estágio alvo

Alfa.

## Decisões relacionadas

- [ADR-0001: Plataforma federativa orientada por contratos](../adr/ADR-0001-contract-oriented-federative-platform.md)
- [ADR-0008: Acordos bilaterais para sistemas autônomos](../adr/ADR-0008-bilateral-integration-agreements.md)
- [ADR-0011: Sistema de Governança da Engenharia do SisTer](../adr/ADR-0011-sge-sister-engineering-governance-system.md)

## Documentos de referência

- [Plano de transição do protótipo para produção](../architecture/sister_transicao_prototipo_para_arquitetura_producao.md)
- [Roteiro Alfa-Beta-Gama](../architecture/sister_roteiro_alfa_beta_gamma_uma_pagina.md)
- [SGE-SisTer](../governance/SGE_SISTER.md)

## Contratos afetados

Novo contrato versionado:

```text
contracts/subsystem/1.0.0/
  README.md
  manifest.schema.json
  capabilities.schema.json
  identity-claims.schema.json
  health.schema.json
  readiness.schema.json
  error.schema.json
  audit-event.schema.json
  openapi.yaml
  examples/
```

O gate Alfa já espera esses artefatos por meio de
`scripts/verify-sister-maturity.sh`.

## Escopo

Incluído:

- definir manifesto mínimo de subsistema;
- definir endpoints internos `/_sister/health`, `/_sister/readiness` e
  `/_sister/capabilities`;
- definir formato comum de erro;
- definir evento mínimo de auditoria;
- definir envelope de identidade que será assinado no WP-05;
- publicar exemplos para Clima e Nexo sem exceção estrutural;
- adicionar validação automatizada dos schemas e exemplos;
- atualizar documentação de integração.

Fora de escopo:

- implementar gateway definitivo;
- remover proxy legado do `sisterd`;
- migrar autorização por capacidades no backend;
- assinar identidade interna em produção;
- adaptar completamente Clima e Nexo.

Esses itens pertencem aos WPs seguintes.

## Critérios de aceite

- `contracts/subsystem/1.0.0/` existe com todos os artefatos esperados pelo
  gate Alfa.
- Exemplos de Clima e Nexo validam contra o mesmo manifesto.
- Health, readiness, capacidades, erro e auditoria possuem schema versionado.
- `openapi.yaml` descreve a superfície interna mínima do subsistema.
- Teste automatizado valida schemas e exemplos.
- `./scripts/verify-sister-maturity.sh --stage alpha --mode check` reconhece
  o contrato como presente.
- Nenhuma exceção estrutural é criada para Clima ou Nexo.

## Evidências esperadas

- schemas versionados em `contracts/subsystem/1.0.0/`;
- exemplos sanitizados para Clima e Nexo;
- teste de contrato executado;
- relatório de maturidade Alfa em modo check;
- atualização do Centro de Engenharia após publicação da atestação.

## Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Contrato amplo demais | Subsistemas implementam superfície desnecessária | separar obrigatório de opcional |
| Contrato específico demais | Clima ou Nexo exigem exceções | validar ambos como exemplos desde o início |
| Capacidades prematuras | WP-02 invade WP-03 | declarar capacidades ofertadas sem resolver autorização final |
| Identidade prematura | WP-02 invade WP-05 | modelar claims sem exigir assinatura operacional ainda |

## Rollback

Como este pacote publica contrato e testes, o rollback consiste em retirar a
versão `contracts/subsystem/1.0.0/` antes de qualquer adaptador depender dela.
Depois que adaptadores consumirem o contrato, mudanças incompatíveis exigem nova
versão.

## Responsável

Papel responsável: Arquitetura do SisTer.
