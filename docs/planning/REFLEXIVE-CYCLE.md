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

Ainda faltam `TechnicalAssessment`, autorização de capacidade, execução,
observação, `OperationalAssessment`, recomendação e realimentação por decisão.

## Regra de conclusão

Uma ação de engenharia pode ser marcada como concluída somente quando a
evidência funcional correspondente existir. Uma transição de cartão, sozinha,
não constitui reflexividade operacional.
