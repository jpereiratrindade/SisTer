# WP-SGE-CONV-01 - Convergência reproduzível do SGE

## Objetivo

Garantir que `./scripts/sge verify` produza avaliação convergente pelos motores
legado e declarativo sem depender de uma execução operacional preexistente.

## Escopo

- usar a mesma evidência para `baseline-integrity` nos dois motores;
- usar o mesmo runner autossuficiente para `smoke-flow`;
- iniciar o `sisterd` do smoke em loopback e porta efêmera;
- encerrar todos os recursos criados pelo smoke;
- exigir quarentena explícita de todo subsistema real registrado;
- excluir candidatos em quarentena antes de resolver repositórios ou perfis;
- impedir regressão por teste executável.

## Fora do escopo

- promoção de subsistemas reais;
- mudança de maturidade funcional;
- autorização G6;
- publicação de gateway ou alteração da fronteira SEC-03V.

## Gate de conclusão

```text
run_quality.sh                       PASS
sge verify / legacy                 PASS
sge verify / declarative            PASS
comparison                          EQUIVALENT
preexisting sisterd                 NOT_REQUIRED
real subsystem without quarantine   REJECTED
```

## Evidências

- `scripts/ci/test-smoke.sh`;
- `scripts/ci/test-reference-contract.sh`;
- `tests/maturity/test_sge_convergence.py`;
- `.run/maturity/components/sister-core/latest.json`.
