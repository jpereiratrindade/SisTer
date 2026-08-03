# WP-EXEC-01 — IntegrationRun

## Objetivo

Materializar uma execução identificável, persistida e reconstruível para o
fluxo Nexo–Compras, servindo de objeto para proveniência e avaliação posterior.

## Estado

Iniciado — contrato versionado validado; tipos, serviço e persistência ainda não iniciados.

## Entregas

- contrato `contracts/execution/1.0.0`;
- gate contratual com metaschema, ciclos positivos e combinações proibidas;
- estados de execução separados de validade;
- idempotência e relações de retry/reprocessamento;
- persistência mínima e API somente após validação do contrato;
- evidência reproduzível de criação e reconstrução.

## Dependências

- `AGR-01` — acordo Nexo–Compras;
- `PROV-01` — ProvenanceRecord;
- `INF-01` — IntegratedInformation.

## Política C++

O modelo de domínio seguirá a [ADR-CPP-01](../adr/ADR-CPP-01-efficient-abstraction-and-polymorphism.md): tipos de valor e agregado encapsulado no núcleo, `std::variant` para alternativas fechadas, transições puras e polimorfismo virtual somente nas portas externas justificadas.

## Fora de escopo

`AssessmentEngine`, ações corretivas, promoção de autoridade e efeitos
operacionais reflexivos.

Análise vetorial também está fora de escopo: `IntegrationRun` registra fatos e
referências; interpretações derivadas seguem a [ADR-VEC-01](../adr/ADR-VEC-01-derived-vector-analysis.md).

Evidência do gate contratual:

```text
./scripts/contracts/validate-integration-run.sh
```

Resultado: schema válido, exemplos de ciclo aceitos, combinações de estado
proibidas rejeitadas e `execution_status` separado de `validity_status`.
