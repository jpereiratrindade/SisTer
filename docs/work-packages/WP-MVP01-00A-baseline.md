# WP-MVP01-00A - Baseline e vocabulário

## Objetivo

Congelar a prova técnica do MVP-00 e separar formalmente prontidão operacional,
arquitetura técnica e participação governada.

## Estado

Concluído quando o gate abaixo passar no commit integrado.

## Entregas

- ADR-0023 aceita;
- baseline `engineering/baselines/mvp-00.json` ligada ao commit `9fac598`;
- digests do contrato técnico e manifesto de referência;
- `IntegrationRun` e `GovernedSystemRegistry` classificados como
  `TESTADO_EM_MEMORIA`;
- distinção entre `PROD-01`, MVP-00 e MVP-01 documentada;
- teste que bloqueia mudança acidental do contrato congelado.

## Gate

```bash
./scripts/ci/test-reference-contract.sh
./scripts/sge verify
```

Resultado exigido: baseline íntegra, SGE `PASS/EQUIVALENT`, nenhum subsistema
real executado e nenhuma autorização operacional inferida.
