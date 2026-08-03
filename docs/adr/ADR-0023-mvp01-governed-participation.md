# ADR-0023 - MVP-01 de Participação Governada e Reflexiva

## Status

Aceita em 2026-08-03 para implementação incremental.

## Contexto

O MVP-00 comprovou núcleo, gateway, contrato técnico e referência controlada.
Essa prova não demonstra legitimidade de participação, decisão humana,
execução governada, proveniência ou avaliação reflexiva ponta a ponta.

`PROD-01` avalia prontidão e autorização operacional do núcleo. Ele não é o
processo funcional do MVP-01 e não pode ser reaberto ou inferido por esta ADR.

## Decisão

O MVP-01 demonstrará participação governada exclusivamente com
`sister_reference`. Subsistemas reais permanecem `QUARANTINED`.

O fluxo normativo será:

```text
candidato -> avaliação técnica -> avaliação de participação -> decisão humana
-> execução -> evidência/proveniência -> avaliação D2/A1/shadow -> explicação
```

A implementação seguirá fatias verticais. `ParticipationContract`, avaliação e
decisão antecedem persistência e execução. Reflexividade começa em D2/A1/shadow
e não bloqueia, corrige ou altera autorização.

Durante o MVP-01, os artefatos congelados em
`engineering/baselines/mvp-00.json` não podem mudar sem nova decisão, nova
versão contratual e atualização explícita da baseline.

## Autoridade

- contrato define condições;
- SGE avalia evidências;
- coordenação humana autoriza participação;
- `sisterd` aplica decisão autorizada;
- maturidade projeta confiança, sem conceder autoridade;
- referência executa capacidade, sem autorizar a si própria.

## Consequências

MVP-01 não promove produção, não autoriza G6 e não reintegra subsistema real.
Tags anteriores permanecem imutáveis. Uma tag futura do MVP-01 somente será
criada após seu gate de encerramento.
