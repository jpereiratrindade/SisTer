# Engenharia SisTer

O diretório `engineering/` reúne o Processo de Engenharia do SisTer, o
SGE-SisTer e seus módulos reutilizáveis.

Toda implementação neste diretório deve evitar dependências irreversíveis do
núcleo da plataforma. A regra é modularizar internamente primeiro, validar em
múltiplos componentes e avaliar extração somente quando houver evidência de
reutilização real.

## Fronteiras

- `process/`: modelos e templates do Processo de Engenharia.
- `governance/`: modelos e templates do SGE-SisTer.
- `maturity/`: perfis, checks e modelos do módulo de maturidade.

Scripts existentes em `scripts/` continuam válidos durante a transição. A
migração para `engineering/` deve ser incremental e preservada por contratos.

## Decisão

Referência: [ADR-0012](../docs/adr/ADR-0012-internal-engineering-modules.md).
