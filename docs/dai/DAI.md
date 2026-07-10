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

## 2026-07-10 - PostgreSQL, PostGIS, pgvector e exposicao

- Decision: planejar PostgreSQL como banco operacional do SisTer, com PostGIS para dados territoriais e pgvector para analises vetoriais.
- Decision: definir escopo `public`, `restricted` e `private` como parte do modelo, da API e das consultas de dashboard.
- Action: documentar arquitetura de banco, ADR e politica publico/privado.
- Impediment: ainda falta migracao SQL executavel e implementacao C++ de persistencia.

## 2026-07-10 - Fronteira federada e DIKW

- Decision: cada contrato de sistema deve declarar acesso direto, politica de compartilhamento, itens nativos da plataforma de origem, escopos publico/restrito/privado e temas sensiveis.
- Decision: adotar a cadeia dado, informacao, conhecimento e sabedoria como linguagem de transformacao da integracao.
- Action: atualizar manifesto, exemplos, interface, DDD e politica publico/privado.
- Impediment: o validador C++ ainda nao verifica os novos campos; por enquanto eles estao formalizados no JSON Schema.

## 2026-07-10 - Radar-Sister Resiliencia como integrante

- Decision: listar `radar_sister_resiliencia` como sistema integrante do SisTer.
- Action: criar manifesto de exemplo e incluir o Radar na interface e na documentacao DDD.
- Impediment: o link local padrao `http://127.0.0.1:8765` depende da GUI do Radar estar em execucao.

## 2026-07-10 - Contratos firmados por sistema

- Decision: diferenciar contratos-base de integracao de contratos firmados por sistema integrante.
- Action: ajustar a home para contar contratos firmados por sistema e criar manifesto de exemplo do CampoNode.
- Impediment: ainda falta persistencia para registrar aceite formal, responsavel e data de assinatura de cada contrato.

## 2026-07-10 - Containers e indicadores demonstrativos

- Decision: recomendar container persistente para PostgreSQL/PostGIS/pgvector e manter a aplicacao local ate existir servidor/API.
- Decision: remover percentual fixo de conformidade da home enquanto a avaliacao automatizada nao existir.
- Action: documentar estrategia de containers e marcar resultados de integracao como demonstrativos.
- Impediment: ainda falta motor real de avaliacao de conformidade e diagnostico.

## 2026-07-10 - Metricas de infraestrutura nos cards

- Decision: exibir metricas de monitoramento de infraestrutura nos cards dos sistemas federados.
- Action: adicionar disponibilidade, resposta/sincronizacao, armazenamento e ultima verificacao na interface.
- Impediment: as metricas ainda sao demonstrativas; falta coletor real conectado a diagnostico, banco ou API dos sistemas.

## 2026-07-10 - Servidor API e banco inicial

- Decision: criar `sisterd` como servidor C++ inicial para interface estatica e endpoints JSON basicos.
- Decision: criar `compose.yml` para PostgreSQL/PostGIS/pgvector com volume persistente.
- Action: adicionar migration inicial e script `scripts/dev/run_postgres.sh`.
- Impediment: a API ainda usa dados em memoria; falta porta de persistencia e integracao real com PostgreSQL.

## 2026-07-10 - Finalizacao operacional do banco

- Decision: expor comandos `sisterctl db-check` e `sisterctl db-migrate`.
- Action: adicionar scripts que usam `psql` local ou `docker exec sister-db psql`.
- Action: registrar migration aplicada em `sister_schema_migrations`.
- Impediment: ainda nao ha repositorio C++ persistindo entidades no PostgreSQL.
