# ADR-0024 - Reflexividade da engenharia e planejamento governado

## Status

Proposta para aprovação em 2026-08-03.

## Contexto

A EFE-SisTer/1.7 define a reflexividade da engenharia como a capacidade de
comparar o estado observado ao modelo-alvo, registrar lacunas, avaliar ações e
preservar a decisão humana sobre prioridades e mudanças de rumo. O PDE-SisTer
materializa esse caminho para o fechamento do MVP-01 com o `sister_reference`.

O SisTer ainda não possui um módulo operacional de planejamento. Construir
primeiro um Kanban ou uma ferramenta genérica de gestão criaria uma projeção
sem fonte de verdade governada.

## Decisão

Implementar a reflexividade da engenharia por uma fatia vertical mínima,
começando pelo registro e explicação de uma única ação ligada ao MVP-01.

O primeiro ciclo será:

```text
DevelopmentGoal -> DevelopmentGap -> DevelopmentAction
-> PriorityAssessment -> PlanningDecision humana
-> evidência -> PlanRevision -> explicação
```

Os objetos persistidos constituem a fonte de verdade. A interface, o Kanban e
qualquer projeção futura não poderão criar, recalcular ou encerrar estados.

## Autoridade e estados

- a EFE define o modelo normativo;
- o RAF registra o estado observado;
- o SGE avalia e recomenda;
- uma autoridade humana registra ou rejeita a decisão de planejamento;
- o work package executa a ação;
- evidências verificáveis sustentam a transição e a revisão do plano.

As ações usam os estados `IDEA`, `ASSESSED`, `PRIORITIZED`, `IN_PROGRESS`,
`VERIFYING` e `COMPLETED`, além de `BLOCKED`, `SUSPENDED`, `SUPERSEDED` e
`REJECTED`. Nenhuma ação pode ser encerrada sem evidência de aceitação.

## Invariantes

- toda ação referencia exatamente um objetivo e uma lacuna;
- toda avaliação de prioridade é recomendação, nunca decisão;
- toda decisão identifica ator, autoridade, escopo, revisão do plano e motivo;
- revisões do plano são imutáveis;
- mudança de EFE, RAF, contrato ou commit pode invalidar evidências e decisões;
- conclusão da ação não implica, por si só, redução ou fechamento da lacuna;
- o SisTer não altera autonomamente EFE, PDE, código, contratos ou prioridades.

## Consequências

O primeiro incremento poderá ser testado sem interface web e sem executar
diretamente pipelines. O `sge plan explain` deverá reconstruir a motivação,
avaliação, decisão, evidência e efeito registrado da ação.

Persistência concreta, concorrência, idempotência, capacidades e formato da
CLI serão definidos nos contratos e work packages correspondentes, não nesta
ADR.
