# Status dos artefatos arquiteturais

Este documento classifica a autoridade dos artefatos do SisTer. Presença no
repositório não significa vigência operacional nem autorização de integração.

## Normativo vigente

Artefatos que governam a baseline atual:

- `contracts/subsystem/1.0.0/`: contrato comum de subsistemas;
- `reference/sister-reference/`: implementação normativa de referência;
- `docs/adr/ADR-0022-reference-subsystem-validation-boundary.md`;
- `docs/governance/SUBSYSTEM_CONFORMANCE.md`;
- `config/run_profiles.json`: cinco perfis executáveis oficiais;
- contratos de gateway, segurança, maturidade, execução e federação que não
  concedam acesso operacional a um subsistema real.

## Histórico preservado

ADRs, evidências, documentos de arquitetura, contratos específicos e testes
anteriores relacionados a Clima, Nexo, Campo, Studio, Compras ou MorfoCampo
registram decisões e comportamento de baselines passadas. Eles não provam
conformidade com `sister.subsystem/1.0.0`, não publicam rotas e não autorizam
execução na baseline atual.

Tags e documentos de release são imutáveis. Uma afirmação histórica deve ser
lida no contexto do commit e da tag aos quais pertence.

## Candidato em quarentena

Registros de recursos, adaptadores, perfis de maturidade e testes específicos
de subsistemas reais podem permanecer como material candidato. Seu estado é
`QUARANTINED` até completar a sequência definida em
`SUBSYSTEM_CONFORMANCE.md` e receber autorização explícita.

Nenhum candidato em quarentena pode:

- ser iniciado por um perfil oficial;
- ser roteado pelo `sisterd` ou pelo gateway;
- aparecer como capacidade operacional na interface;
- servir como evidência de prontidão do núcleo;
- tornar-se autorizado apenas porque responde a uma rota histórica.

## Drafts de arquitetura sem vigência operacional

`sister.participant/2.0.0`, `sister.capability-invocation/1.0.0` e
`sister.relation/1.0.0` são drafts do ARC-01. Eles não são normativos para o
runtime, não substituem `sister.subsystem/1.0.0` e não autorizam integração,
rota, persistência ou execução. Seu propósito é estabilizar a semântica antes
de qualquer experimento de transporte.

## Regra de precedência

Em conflito, prevalecem nesta ordem:

1. contrato normativo vigente;
2. ADR vigente mais recente;
3. política de governança vigente;
4. documentação operacional vigente;
5. material histórico ou candidato, sem autoridade operacional.
