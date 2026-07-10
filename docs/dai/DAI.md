# DAI - SisTer

## 2026-07-09

- Decision: iniciar o SisTer como plataforma federativa de convergencia territorial orientada por contratos.
- Action: criar scaffold C++20 governado com contratos, DDD, ADR, politicas, exemplos e validadores.
- Impediment: nenhuma dependencia externa de JSON Schema foi adotada ainda; validacao C++ inicial cobre apenas invariantes minimas.

## 2026-07-10

- Decision: incluir uma primeira interface estatica antes do servidor para validar linguagem, navegacao e leitura dos contratos.
- Action: criar `web/index.html`, `web/styles.css` e `web/app.js` com visao geral, sistemas, contratos, evidencias e mapa territorial sintetico.
- Impediment: a interface ainda usa dados demonstrativos embutidos; a ligacao com `sister_core` deve vir por API ou export JSON em incremento posterior.

## 2026-07-10 - Identidade Radar e novas funcoes

- Decision: alinhar a identidade visual inicial do SisTer ao Radar-Sister Resiliencia, com topo horizontal, cards institucionais, dashboard compacto e rodape de governanca, LGPD e seguranca.
- Decision: separar `Integracao e transformacao de conhecimento` de `Sintese tecnica e diagnostico dos servicos`.
- Action: atualizar a interface para home com cards classicos de sistemas, barras de resultado de integracao, painel de integracao/conhecimento e painel de diagnostico tecnico.
- Impediment: os indicadores ainda sao demonstrativos; o proximo passo e alimentar a UI a partir de arquivos JSON exportados pelo core ou por uma API local.
