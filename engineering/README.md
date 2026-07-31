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

Scripts existentes em `scripts/` continuam válidos durante a transição. O
módulo de maturidade já usa perfis e checks em `engineering/maturity/`, mas o
avaliador e o publicador ainda vivem em `scripts/maturity/`. Essa separação é
transitória e deve ser preservada por contratos.

Uso principal para executar qualidade e maturidade de todos os componentes
localmente resolvíveis:

```bash
./scripts/sge verify
```

Para uma avaliação de maturidade específica:

```bash
./scripts/sge maturity publish pre-alpha
```

Tutorial específico: [maturity/README.md](./maturity/README.md).

## Decisão

Referência: [ADR-0012](../docs/adr/ADR-0012-internal-engineering-modules.md).
