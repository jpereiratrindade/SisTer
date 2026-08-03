# ADR-VEC-01: Análise vetorial como capacidade analítica derivada

## Status

Aceita como direção futura; implementação não iniciada.

## Contexto

O SisTer poderá usar vetores operacionais, embeddings semânticos e SIMD para
comparação, visualização e investigação. Esses mecanismos produzem
interpretações derivadas e não devem alterar o significado factual de uma
execução nem substituir contratos, estados, digests, autoridade ou proveniência.

## Decisão

- vetores não pertencem ao agregado `IntegrationRun`;
- resultados vetoriais serão `DerivedEvidence` identificados e versionados;
- toda vetorização dependerá de um `VectorizationProfile` versionado;
- método, features, unidades, normalização, baseline, métrica e versão serão
  preservados;
- comparação vetorial não substituirá validação determinística;
- o primeiro uso será em `shadow`, sem gate, efeito ou ação automática;
- embeddings produzirão candidatos analíticos, não correlações confirmadas;
- dados sensíveis não poderão ser inferidos ou expostos pelo vetor;
- SIMD só será adotado após benchmark reproduzível.

## Separação de responsabilidades

```text
IntegrationRun       fatos da execução
AnalysisVector       representação numérica derivada
VectorComparison     comparação analítica
DerivedEvidence      evidência produzida
OperationalAssessment juízo governado
```

Uma futura análise deverá referenciar `RunId`, `SchemaId`, `Digest` e
`EvidenceId` de origem e de saída. O algoritmo conhece referências e contratos,
não redefine o agregado factual.

## Dependências e sequência

`VEC-LAB-01` aguarda `EXEC-01`, `PROV-01` e `INF-01`. A decisão não altera a
prioridade atual de `EXEC-01B`, nem libera `REF-01` ou o `AssessmentEngine`.
