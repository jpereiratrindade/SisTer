# WP-SGE-PLAN-01 - Primeiro ciclo de planejamento reflexivo

## Estado

`EM_IMPLEMENTACAO` — incremento consultivo e decisão controlada; não é gate de
release nem promoção de maturidade.

## Objetivo

Materializar a infraestrutura consultiva do PDE-SisTer para o `GOAL-MVP01`, demonstrando
que uma recomendação de prioridade permanece separada da decisão humana e da
transição de estado.

Este WP é auxiliar. O ciclo funcional principal do MVP-01 é a reflexividade
operacional da participação: execução, observação, evidência, avaliação,
recomendação e decisão.

## Entregas

- contratos mínimos de planejamento 1.0.0;
- `engineering/planning/plan.json` como estado inicial versionado;
- validação específica do plano;
- `sge plan status|list|gaps|show|explain`;
- `sge plan assess` com recomendação sem mutação;
- `sge plan decision record` para decisão humana explícita;
- `sge plan transition` com autorização de transição, validade e uso único;
- `PlanRevision` gerada pela transição autorizada;
- teste automatizado do ciclo em plano temporário.

## Invariantes

- assessment não autoriza e não altera estado;
- decisão registrada não executa transição automaticamente;
- a autorização deve declarar a transição exata;
- decisão usada não pode autorizar uma segunda transição;
- o plano versionado do repositório permanece em `IDEA` até decisão real;
- nenhuma tag ou baseline de release é alterada.

## Evidências

```bash
python3 scripts/planning/validate.py
python3 tests/planning_contract_test.py
python3 scripts/sge plan explain PDE-MVP01-01
```

## Fora do escopo

Kanban editável, API web de decisão, autorização de produção e execução
automática de work packages. A interface web consultiva não substitui o ciclo
operacional da participação.
