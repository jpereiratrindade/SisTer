# Arquitetura SGR

O SGR, no contexto do SisTer, é tratado como parte do sistema de governança
da engenharia. Ele verifica maturidade, preserva evidências e separa resultado
técnico de autoridade de promoção.

## Documentos

- [Engines de verificação e modos de governança](./verification-engines-and-governance-modes.md): referência canônica sobre `legacy`, `declarative`, `compare`, `shadow` e `governed`.
- [Centro de Engenharia do SisTer](../MATURITY_DASHBOARD.md): página operacional e de produto que apresenta os resultados do SGR.
- [Troubleshooting de divergências](../../operations/sgr/troubleshooting-verification-divergence.md): procedimento operacional para divergências entre engines.

## Política sintética

O engine determina como a maturidade é verificada; o modo de governança
determina que autoridade o resultado possui.

`compare` protege a migração do verificador; `shadow` protege a evolução
federada do ecossistema.
