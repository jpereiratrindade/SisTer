# Contratos de integração - 1.0.0

Primeira unidade operacional reflexiva do SisTer.

Uma integração nasce quando uma oferta de capacidade de um subsistema satisfaz uma necessidade publicada por outro subsistema. O Centro de Engenharia detecta a candidata, a engenharia aprova objetivo, mapeamentos, transformações e critérios, e o SisTer passa a executar, observar, comparar e recomendar.

## Contratos

- `CapabilityOffer`: o que um subsistema oferece.
- `CapabilityRequirement`: o que um subsistema necessita.
- `IntegrationDefinition`: integração candidata ou aprovada entre oferta e necessidade.
- `IntegrationDecision`: aprovação ou rejeição humana rastreada.
- `IntegrationExecution`: execução concreta de uma integração aprovada.
- `OperationalAssessment`: comparação esperado x observado e recomendação.

## Ciclo mínimo

```text
CapabilityOffer
-> CapabilityRequirement
-> IntegrationDefinition aprovada
-> IntegrationDecision
-> IntegrationExecution
-> OperationalAssessment
```

O SisTer não altera automaticamente uma integração aprovada. Ele registra execução, observa resultado, compara com critérios e recomenda ações para a engenharia.
