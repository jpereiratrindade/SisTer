# Primeiro ciclo reflexivo operacional

O plano e o Centro de Engenharia orientam o trabalho, mas o objetivo funcional
do MVP-01 é fechar este ciclo:

```text
contrato esperado
→ participação proposta
→ capacidade autorizada
→ execução no sister_reference
→ resultado observado
→ evidências e proveniência
→ comparação com o contrato
→ OperationalAssessment
→ recomendação
→ decisão humana
→ nova condição de execução
```

O ciclo de engenharia (`objetivo → lacuna → ação → evidência → revisão`) é uma
camada auxiliar para construir e tornar esse ciclo visível. Não deve ser usado
como substituto da reflexividade operacional.

## Estado atual

O SisTer já possui a entrada do ciclo:

```text
identidade autenticada
→ proposta
→ validação inicial
→ persistência PostgreSQL
→ consulta
```

O primeiro `participation-assessment` técnico agora pode ser produzido a partir
do contrato validado. Ele registra PASS, digest, commit e limitações, mas seu
efeito de gate é `none` e sua recomendação ainda exige decisão humana.

O próximo registro observável é restrito ao processo
`P-MVP01-PARTICIPATION`. A migração `010_participation_timeline.sql` reserva uma
timeline mínima para `ParticipationProposed` e
`TechnicalAssessmentCompleted`, sem criar um barramento genérico de eventos.

O Centro de Engenharia deve apresentar esse processo como uma sequência de
funções cumpridas — proposta, avaliação, decisão, autorização, execução e
reavaliação. Documentos, scripts e testes são sustentação e evidência dessas
funções, não o processo em si.

O `TechnicalAssessment` já é produzido localmente e a persistência autoritativa
está preparada. Ainda falta integrá-lo à timeline, registrar a decisão humana,
autorizar capacidade, executar, observar, produzir `OperationalAssessment` e
realimentar a próxima condição por decisão.

## Regra de conclusão

Uma ação de engenharia pode ser marcada como concluída somente quando a
evidência funcional correspondente existir. Uma transição de cartão, sozinha,
não constitui reflexividade operacional.
