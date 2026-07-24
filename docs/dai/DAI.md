# DAI - SisTer

## 2026-07-24 - Continuidade de sessão e referência climática

- Decision: o acesso ao Sister-Clima deve transportar a origem exata da
  instância autenticada do SisTer, permitindo retorno à mesma porta e ao mesmo
  armazenamento de sessões.
- Decision: o card do Sister-Clima deve identificar os produtos climáticos e
  suas fontes, sem incorporar respostas brutas ou parâmetros privados.
- Action: adicionar `sister_url` ao link restrito, validá-lo no produtor pelo
  mesmo host e apresentar precipitação diária, Open-Meteo e NASA POWER no card
  e no detalhe do sistema.
- Impediment: as sessões ainda residem em memória por processo; continuidade
  entre instâncias diferentes exigirá armazenamento de sessão compartilhado.

## 2026-07-24 - Contexto da Plataforma Colaborativa Sul

- Decision: apresentar o SisTer discretamente como atividade sobre as bases de
  sistemas inteligentes de governança no âmbito do Projeto Plataforma
  Colaborativa Sul da Embrapa.
- Evidence: a Carta Anual de Políticas Públicas e Governança Corporativa 2025
  da Embrapa, página 13, relaciona a transformação de dados isolados a sistemas
  inteligentes de governança e apresenta a Plataforma Colaborativa Sul na mesma
  seção de expansão de tecnologias validadas.
- Action: inserir nota institucional na home pública com link direto à fonte,
  sem atribuir à publicação menção nominal ao SisTer.

## 2026-07-24 - Referência institucional à Embrapa

- Decision: apresentar a relação institucional como `Projeto Resiliência ·
  Embrapa`, sem caracterizá-la como patrocínio, endosso comercial ou
  titularidade do SisTer.
- Decision: usar chamada textual e link para o portal oficial; a marca gráfica
  dependerá de ativo oficial e da validação de uso aplicável.
- Action: incluir acesso a `https://www.embrapa.br/` na barra superior e no
  rodapé, abrindo em nova aba com proteção de contexto.

## 2026-07-24 - Home pública sem inventário federado

- Decision: apresentar a pessoas não autenticadas somente a ideia central do
  SisTer como sistema de inteligência territorial governada, sem nomes,
  quantidades, estados, vínculos ou detalhes dos sistemas federados.
- Action: tornar `/api/systems` e o JavaScript do painel recursos autenticados,
  eliminar o carregamento inicial do catálogo e adotar uma home pública
  institucional sem métricas operacionais.
- Action: esta decisão substitui a divulgação pública de existência prevista
  nas decisões de acesso e integração do Sister-Clima de 2026-07-23.
- Impediment: a página HTML contém a estrutura vazia do painel para hidratação
  após o login; dados e inventário permanecem ausentes dos recursos públicos.

## 2026-07-24 - Governança não comercial do Sister-Clima

- Decision: autorizar a promoção de resultados revisados do Sister-Clima para
  usuários identificados, exclusivamente em pesquisa pública e apoio
  institucional sem finalidade lucrativa ou comercial.
- Action: adotar `sister-clima.governance/1.0.0`, explicitar atribuição,
  proveniência, cotas, GPL, fontes, resultados permitidos e gatilhos de revisão.
- Impediment: a origem Streamlit não possui autenticação própria; deve
  permanecer em loopback até existir proxy reverso autenticado ou controle
  equivalente.

## 2026-07-23 - Acesso restrito ao Sister-Clima

- Decision: manter a descoberta do Sister-Clima no catalogo publico, sem expor
  sua URL de acesso. **Substituída em 2026-07-24 pela home pública sem
  inventário federado.**
- Action: classificar o link como restrito e entrega-lo por endpoint que exige
  uma sessao autenticada no SisTer.
- Impediment: a autenticacao protege a entrega do link pelo SisTer; a aplicacao
  de origem ainda precisa de controle proprio caso seja exposta fora do host
  local.

## 2026-07-23 - Integracao do Sister-Clima

- Decision: reconhecer `sister_clima` como sistema climatico federado, mantendo
  a experiencia analitica e as consultas interativas na plataforma de origem.
- Action: reservar a porta local 8501, publicar o sistema no catalogo e em
  `/api/systems`, reconhecer seu manifesto e documentar a fronteira do
  adaptador.
- Impediment: a ingestao automatica de arquivos climaticos ainda nao foi
  implementada; nesta fase, `file_import` descreve importacao controlada por
  contrato.

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
