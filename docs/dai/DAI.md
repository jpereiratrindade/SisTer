# DAI - SisTer

## 2026-07-30 - Nexo ampliado para portfólio multiprojeto

- Decision: `nexo_projects` é a fonte de verdade e Aggregate raiz dos projetos
  científicos; o SisTer não mantém cadastro concorrente.
- Decision: o Projeto Resiliência permanece como dado fundador migrado e deixa
  de funcionar como contexto implícito no código e nas interfaces.
- Decision: desafios e atividades exigem `project_id` explícito e uma atividade
  somente pode referenciar desafio do mesmo projeto.
- Decision: o Compras mantém visão autenticada do acervo completo; projeto é
  referência atribuível e filtro opcional, não condição de existência.
- Action: disponibilizar a seção **Projetos** no Nexo para cadastro, edição,
  estado, período, instituição líder, equipe e indicadores.
- Action: resolver autorizações e projeções Nexo–Compras pelo vínculo de projeto
  contratado, sem identificador fixo.

## 2026-07-29 - Integração Nexo–Nexo-Compras concluída

- Decision: o Nexo é a autoridade para projetos, ações, atividades, estrutura
  de pesquisa, evidências e produtos científicos.
- Decision: compras permanece um contexto autônomo, ligado a projetos e
  atividades por identificadores e contratos, sem banco compartilhado.
- Decision: `Nexo-Compras` é o nome do produto; `sister_compras` permanece como
  identificador técnico compatível.
- Decision: a relação contratual é SisTer–Nexo–Nexo-Compras. O SisTer não
  cataloga nem acessa o Compras como subsistema direto.
- Action: reservar `8016` e `55440`, com banco, container e volume exclusivos.
- Action: preparar `/integrations/nexo/compras/` no proxy do Nexo; a rota não é
  autorizada nem publicada pelo SisTer `v0.2.7`.
- Action: preservar os dados migrados e o volume anterior para rollback.

## 2026-07-28 - SisTer-Campo federado e canais CampoSync

- Decision: registrar o SisTer-Campo como sistema federado com identidade, API
  e PostgreSQL proprios, sem banco compartilhado com o SisTer.
- Decision: API local e pacote offline transportam o mesmo contrato
  `camposync.package/1.0.0`; conectividade nao altera a semantica dos dados.
- Decision: o MorfoCampo permanece produtor autonomo, enquanto o SisTer-Campo
  valida, registra, cura e preserva proveniencia antes da promocao ao SisTer.
- Decision: pacotes CampoSync sao restritos; audio, fotos, identidade de
  operador e auditoria permanecem privados por padrao.
- Action: reservar `127.0.0.1:8013` para a API e `55438` para o PostgreSQL do
  SisTer-Campo.
- Impediment: a promocao de dados curados para o catalogo territorial do SisTer
  ainda requer endpoint e teste de aceitacao especificos.

## 2026-08-02 - Resultado composto e perfis do run_all

- Decision: qualidade do núcleo, prontidão do `sisterd` e disponibilidade dos
  subsistemas são dimensões distintas no relatório de execução.
- Decision: falha opcional produz `PASS_WITH_DEGRADATION`; componente exigido
  pelo perfil produz `BLOCKED` e código `2`.
- Decision: `dev-core`, `dev-ecosystem`, `dev-ecosystem-strict`, `test-core` e
  `sec-03v` são contratos versionados; o último valida pré-requisitos, mas não
  fecha o gate SEC-03V.
- Decision: `quality.json` descreve somente a qualidade da árvore;
  `run-all-status.json` consolida banco, serviço, smoke e subsistemas.
- Decision: resumos operacionais nunca imprimem credenciais, e `run_all.sh`
  inicia o artefato já testado sem recompilação posterior.
- Decision: mudança de fontes não executa reconciliação implicitamente; ela
  exige `--update-subsystems`.
- Action: registrar por componente estado, fase, código, duração, log e origem
  da inicialização em `.run/maturity/subsystems.json`.

## 2026-08-02 - Quarentena também no bind de desenvolvimento

- Decision: o listener TCP de desenvolvimento e teste do `sisterd` aceita
  somente loopback IPv4; `0.0.0.0` deixa de ser o padrão de desenvolvimento.
- Decision: acesso por outro equipamento deve atravessar uma fronteira de
  laboratório governada, sem publicar diretamente o listener do `sisterd`.
- Action: substituir a reserva `0.0.0.0:8000` por `127.0.0.1:8000` e sanitizar
  variáveis `SISTER_*` herdadas nos testes negativos.
- Supersedes: a decisão de bind do `sisterd` em desenvolvimento registrada em
  2026-07-28; a decisão do Sister-Clima em `0.0.0.0:8501` não é alterada.

## 2026-07-28 - Ponto de entrada e bind por ambiente

- Decision: o SisTer é o ponto de entrada do ecossistema integrado; projetos
  federados continuam autônomos, mas não iniciam a plataforma superior.
- Decision: o Sister-Studio permanece o orquestrador exclusivo de composição,
  voz e vídeo quando executado isoladamente.
- Action: documentar `SisTer/scripts/run_all.sh dev 8000` como fluxo canônico
  para catálogo, autenticação federada e subsistemas.
- Action: tornar o bind do `sisterd` explícito por ambiente, usando
  `0.0.0.0:8000` em desenvolvimento e `127.0.0.1:8001` em teste.
- Decision: o bind de desenvolvimento permite acesso somente na rede local
  governada e não autoriza exposição direta à internet.
- Decision: o SisTer é a autoridade de credenciais; subsistemas reutilizam sua
  sessão e não definem uma segunda senha federada.
- Action: permitir a migração explícita de uma identidade ativa do
  Sister-Studio, preservando seu UUID e solicitando uma nova senha somente no
  terminal local.
- Decision: o Sister-Clima usa `0.0.0.0:8501` apenas no desenvolvimento em LAN
  controlada para preservar a sessão entre portas; publicação externa exige
  proxy autenticado e backend em loopback.

## 2026-07-24 - Primeiro ciclo somente com Clima e Studio

- Decision: o primeiro ciclo integrado e automatizado contém somente
  Sister-Clima e Sister-Studio.
- Decision: MorfoCampo, DroneOps, Radar-Sister e CampoNode deixam
  temporariamente o catálogo, as evidências demonstrativas e a inicialização
  automática do SisTer.
- Decision: as reservas locais `8011`, `8012` e `8765` permanecem no registro
  para impedir colisões; CampoNode continua apenas como projeto planejado.
- Decision: os repositórios e processos autônomos não são apagados nem
  encerrados por este descadastro; uma futura reintegração exige decisão e
  contrato explícitos.

## 2026-07-24 - Inicialização governada dos subsistemas

- Decision: o SisTer verifica, ao subir em desenvolvimento, os subsistemas
  integrados cuja política local seja `ensure-running`.
- Decision: saúde, repositório, comando, ambiente, prazo e criticidade são
  declarados em `config/local_resources.json`; o orquestrador não infere nem
  executa comandos fora dessa lista.
- Action: preservar serviços saudáveis, iniciar os indisponíveis com processo
  destacado, aguardar prontidão e manter logs em `.run/subsystems/`.
- Decision: a sonda HTTP confirma status e identidade do serviço; uma porta
  ocupada com resposta inválida impede reinício duplicado, mas é reportada como
  degradação em vez de ser considerada saudável. A espera informa progresso a
  cada dez segundos.
- Decision: subsistemas conteinerizados podem declarar fontes monitoradas; uma
  mudança reconcilia a aplicação pelo comando governado e registra o conteúdo
  aplicado, preservando volumes de dados.
- Decision: o ambiente de teste não inicia dependências; degradações opcionais
  são informadas e o modo estrito permanece disponível para operação assistida.

## 2026-07-24 - Sessão federada do Sister-Studio

- Decision: o acesso humano ao Sister-Studio reutiliza a sessão já validada no
  SisTer, sem solicitar novamente e-mail ou senha.
- Decision: manter `8443` como fronteira HTTPS do Studio; a mudança de porta
  representa a entrada do subsistema, não uma troca de identidade.
- Action: transportar `sister_url` no link, validar `sister_session` em
  `/api/me` somente nas portas locais autorizadas e encaminhar internamente
  apenas UUID, papel e autoridade.
- Decision: usar `SameSite=Lax` no cookie de sessão para permitir que ele
  acompanhe a navegação GET de nível superior de `http://SisTer` para
  `https://Sister-Studio`; requisições mutáveis continuam protegidas contra
  envio entre sites. Em produção, o SisTer também deve operar em HTTPS e emitir
  o cookie com `Secure`.
- Impediment: certificados de desenvolvimento continuam exigindo confiança
  local; publicação externa requer certificado institucional e ratificação do
  registro de tratamento da identidade federada.

## 2026-07-24 - Fronteira híbrida e resumo climático local

- Decision: manter o Sister-Clima em Streamlit como produtor analítico enquanto
  autenticação, governança, catálogo e resumos permanecem no SisTer C++.
- Decision: migrar capacidades para C++ por contrato e somente quando coleta,
  transformações e formatos estiverem estáveis, sem reescrita integral imediata.
- Decision: localização não será inferida silenciosamente; a consulta começa
  somente após ação do usuário, usa geolocalização do navegador em contexto
  seguro ou localização aproximada por IP em HTTP, reduz coordenadas a duas
  casas decimais e não as armazena no SisTer.
- Action: ampliar a área útil do painel e oferecer no card climático uma
  consulta transitória do acumulado modelado dos seis dias anteriores e de
  hoje, com atribuição ao Open-Meteo.
- Impediment: a consulta direta depende de serviços externos; o fallback por IP
  é impreciso e exige revisão institucional de privacidade antes da produção.

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
- Impediment: ~~a interface ainda usa dados demonstrativos embutidos; a ligacao com `sister_core` deve vir por API ou export JSON em incremento posterior.~~ **Resolvido em 2026-07-30**: sistemas e contratos agora sao lidos do PostgreSQL via libpq.

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
- Impediment: ~~a API ainda usa dados em memoria; falta porta de persistencia e integracao real com PostgreSQL.~~ **Resolvido em 2026-07-30**: `sisterd` conecta ao PostgreSQL via libpq; fallback automatico sem banco.

## 2026-07-10 - Finalizacao operacional do banco

- Decision: expor comandos `sisterctl db-check` e `sisterctl db-migrate`.
- Action: adicionar scripts que usam `psql` local ou `docker exec sister-db psql`.
- Action: registrar migration aplicada em `sister_schema_migrations`.
- Impediment: ~~ainda nao ha repositorio C++ persistindo entidades no PostgreSQL.~~ **Resolvido em 2026-07-30**: `DbConn` lida sistemas, contratos, evidencias e diagnosticos diretamente das tabelas via `row_to_json()`.

## 2026-07-30 - Persistencia PostgreSQL no sisterd

- Decision: conectar `sisterd` ao PostgreSQL via `libpq` (C), sem nova dependencia externa; unica conexao persistente com reconexao supervisionada.
- Decision: manter literais estaticos como fallback explicito; servidor opera sem banco sem interrupção.
- Action: criar `db.hpp`/`db.cpp` com `DbConn` (RAII), `ensureConnected()` e metodos `query*()` usando `row_to_json()` do banco.
- Action: atualizar `CMakeLists.txt` com `find_package(PostgreSQL)` opcional e definicao `SISTER_HAVE_LIBPQ`.
- Action: aplicar `004_seed_systems.sql` com os 4 sistemas canonicos e 3 contratos adicionais.
- Action: instalar `libpq-devel` no toolbox `fedora-44-sister`.
- Impediment: dados territoriais (objetos geoespaciais) ainda sao demonstrativos; falta coletor real para `/api/diagnostics`.
