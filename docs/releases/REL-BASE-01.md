# REL-BASE-01 — Baseline integrada v0.2.10

## Estado

Baseline corrente de integração e governança de release.

## Regra de convergência

Nesta baseline, a linha principal, o arquivo `VERSION`, a documentação corrente
e a tag de release devem apontar para a mesma revisão integrada. Tags anteriores
permanecem imutáveis e conservam seu significado histórico.

## Mapa de releases

| Release | Significado |
| --- | --- |
| `v0.2.7` | identidade interna assinada e SEC-02 sob escopo restrito |
| `v0.2.8` | contratos de reflexividade operacional `REF-00` |
| `v0.2.9` | contrato `EXEC-01A`, política C++ e análise vetorial derivada |
| `v0.2.10` | baseline integrada em `main`, com `VERSION`, documentação e gates reconciliados |

## Conteúdo corrente

- `SEC-03V` validado tecnicamente;
- `REF-00` concluído e validado;
- `EXEC-01A` concluído e validado;
- `ADR-REF-01`, `ADR-CPP-01` e `ADR-VEC-01` registradas;
- `EXEC-01B` é o próximo incremento técnico;
- `FED-01`, `AGR-01`, `PROV-01`, `INF-01`, `SGE-01` e `REF-01` permanecem nos estados documentados em seus pacotes e dependências.

## Limites

Esta release não declara o `AssessmentEngine`, ações corretivas, exposição
externa, `FED-01`, `AGR-01` ou a execução Nexo–Compras completa como concluídos.
O `docs.zip` local não faz parte da baseline versionada.

## Gate de publicação

```text
[x] main recebe fast-forward da branch integrada
[x] VERSION = 0.2.10
[x] validadores REF-00 e EXEC-01 passam
[x] build/testes/gates da baseline passam
[x] tags anteriores preservadas
[x] worktree limpo, exceto artefatos locais explicitamente não versionados
```
