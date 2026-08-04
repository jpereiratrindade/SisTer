# PDE-SisTer/1.0

Plano inicial de desenvolvimento evolutivo derivado da EFE-SisTer/1.7 e do
RAF-SisTer/1.0.

## Estado de materialização

O primeiro ciclo está implementado parcialmente pelo
[`WP-SGE-PLAN-01`](../work-packages/WP-SGE-PLAN-01.md). A superfície CLI já
permite consultar, explicar, avaliar, registrar decisão e aplicar uma transição
autorizada em uma cópia de plano. O plano versionado neste repositório continua
em `IDEA`; nenhum estado de release ou tag é alterado por este incremento.

## Objetivo vigente

`GOAL-MVP01` — fechar o ciclo de participação governada e reflexiva com o
`sister_reference`, antes de reintegrar subsistemas reais ou iniciar
contextualização científica.

O Centro de Engenharia é uma projeção consultiva do plano. A reflexividade
principal do MVP-01 permanece o ciclo operacional de participação:
execução, observação, evidência, avaliação, recomendação e decisão.

## Primeira ação governada

`PDE-MVP01-01` — persistir a candidatura e o contrato de participação.

### Critério de aceitação

O contrato da referência deve poder ser registrado, consultado e reconstruído
com versão, digest, owner, autoridades, capacidades, contribuições e estado
`proposed`, sem edição direta da persistência.

### Evidências esperadas

- schema e exemplo válidos;
- teste de validação e rejeição;
- decisão humana vinculada à ação;
- execução do work package no commit avaliado;
- relatório de teste reproduzível.
- endpoint HTTP autenticado preliminar e consulta pelo `sisterd`;
- confirmação de que o armazenamento local experimental não é fonte de verdade.

### Estado inicial

`IDEA`. A priorização e a transição dependem da decisão humana registrada pelo
SGE.

## Regra de revisão

Qualquer mudança de EFE, RAF, contrato, baseline ou commit deve provocar nova
avaliação da ação e pode invalidar decisões ou evidências anteriores.

O PDE é um plano versionado. O Kanban, quando implementado, será somente uma
projeção dos objetos persistidos.
