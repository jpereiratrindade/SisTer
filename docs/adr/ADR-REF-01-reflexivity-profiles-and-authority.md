# ADR-REF-01: Perfis e autoridade da reflexividade operacional

## Status

Aceita para o piloto Nexo–Compras; promoção de autoridade ainda não autorizada.

## Contexto

A EFE-SisTer/1.4 estabeleceu que o SisTer deve ser amplamente reflexivo, mas apenas seletivamente autocorretivo. Antes da codificação, é necessário congelar o contrato mínimo que impede que cada componente crie seu próprio modelo de observação, decisão e correção.

## Decisão

O piloto usará um `ReflexivityProfile` versionado. O perfil declara, no mínimo:

- `profile_id`, versão, capacidade/processo e escopo;
- profundidade `D0–D5`, autoridade `A0–A5` e modo operacional;
- `ReferenceSnapshot`, avaliador e versão do avaliador;
- evidências obrigatórias, tolerâncias, severidades e política de falha;
- efeito de gate (`shadow`, `pass`, `warn` ou `block`);
- ações permitidas, owner de autorização, reversão e retenção.

O perfil inicial será `RFP-NC-01`, aplicado à integração Nexo–Compras em `D2–D3/A1/shadow`.

## Contratos de resultado e ação

`OperationalAssessment` deverá registrar a execução avaliada, referência vigente, evidências, avaliador, versão, resultado, severidade, limitações, confiança, explicação, efeito de gate e resposta proposta.

Resultados mínimos: `confirmed`, `divergent`, `inconclusive` e `not_applicable`. Resultado, severidade, gate e ação são dimensões independentes.

Uma `CorrectiveAction` será um registro separado, com proposta, autoridade, aprovação, precondições, aplicação, efeitos esperados, reversão, estado e verificação posterior. Uma divergência, por si só, nunca concede autoridade para corrigi-la.

## Interfaces C++ mínimas

As interfaces devem manter avaliação e execução separadas:

```cpp
EvidenceBundle EvidenceCollector::collect(const ExecutionContext&);
OperationalAssessment AssessmentEngine::assess(
    const EvidenceBundle&, const ReferenceSnapshot&, const EvaluatorVersion&);
ActionDecision ReflexivityPolicy::authorize(
    const OperationalAssessment&, const ReflexivityProfile&);
ExecutionReceipt CorrectiveActionExecutor::apply(const AuthorizedAction&);
```

No primeiro incremento, `ReflexivityPolicy` não autoriza efeito operacional nem ação corretiva. O `CorrectiveActionExecutor` permanece fora do caminho do piloto.

## Persistência e proveniência

Cada avaliação deve ser reproduzível a partir de identificadores ou digests da execução, perfil, referências, evidências, avaliador e versão. A evidência original não pode ser apagada ou substituída pela avaliação. Reavaliações geram novos registros relacionados ao anterior.

Evidência insuficiente produz `inconclusive` ou `not_applicable`, conforme o perfil; nunca autoriza inferência silenciosa, correção ou promoção de maturidade.

## Limites do modo `shadow`

No modo `shadow` o sistema pode coletar, comparar, explicar, persistir e recomendar. Não pode bloquear, cancelar, isolar, reverter, suspender, reprocessar nem alterar a execução avaliada. A atestação deve declarar explicitamente: **nenhum efeito operacional**.

## Critérios de promoção

Não haverá promoção de A1 para A2 ou A3 apenas por decisão do avaliador. A proposta de promoção exige, no mínimo:

1. histórico suficiente de avaliações reproduzíveis;
2. taxa e causas de inconclusão conhecidas;
3. testes de falha, conflito e duplicação de evidências;
4. política explícita para a ação pretendida;
5. escopo mínimo, reversibilidade e verificação posterior comprovadas;
6. ADR ou alteração formal do perfil aprovada pelo owner competente.

A2 pode recomendar ou solicitar aprovação. A3 só poderá proteger uma invariante previamente definida e autorizada. Nenhuma promoção altera a exigência de governança humana para contratos, critérios científicos, políticas, código ou finalidade.

## Consequências

- O piloto experimenta o juízo reflexivo sem entregar um “martelo” operacional ao sistema.
- Avaliador, gate e executor podem evoluir e ser testados independentemente.
- A rastreabilidade passa a ser requisito do contrato, não característica incidental do código.
- O próximo trabalho é REF-00: tipos, schemas e contratos centrais; em seguida REF-01: avaliador `shadow` Nexo–Compras.

## Relações

- EFE-SisTer/1.4 — [especificação arquitetural](../architecture/EFE_SISTER_1_4_REFLEXIVIDADE_CPP.tex)
- [Comunicado à equipe](../governance/COMUNICADO_REFLEXIVIDADE_OPERACIONAL_V1.md)
