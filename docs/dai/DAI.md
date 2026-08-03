# DAI - SisTer

## 2026-08-03 - Subsistema de referência como alvo normativo

- Decision: suspender integração operacional dos subsistemas reais e marcar
  seus contratos de execução como `quarantined` e `operational_access: false`.
- Decision: usar `sister_reference` como único alvo funcional, operacional e de
  segurança dos perfis oficiais.
- Decision: preservar ADRs, contratos, evidências e tags históricas; quarentena
  não apaga história nem certifica integração futura.
- Action: substituir catálogo, rotas, perfis e CTest operacionais pela referência
  parametrizada em loopback.
- Evidence: `sisterd_reference_integration_tests`, contrato de perfis e manifesto
  de execução demonstram identidade mediada, echo, queda e preservação do núcleo.
- Impediment: subsistemas reais só retornam após processo de conformidade definido
  em ADR-0022.

## 2026-08-03 - Superfície operacional e ownership do run_all

- Decision: manter `sisterd` em loopback nos perfis locais e em socket Unix no
  perfil LAN; somente gateway federador SisTer pode publicar `8443`.
- Decision: `dev-ecosystem` declara `LOCAL_ONLY` e gateway `NOT_REQUESTED`;
  `dev-lan` declara `LAN_FEDERATED` e exige gateway `READY` para obter `PASS`.
- Decision: subsistema orquestrado deve declarar endpoint HTTP interno,
  health check contratual e nenhuma escuta wildcard.
- Decision: cada execução registra processos, grupos e contêineres próprios;
  teardown preserva recursos encontrados antes da execução.
- Action: validar superfície no contrato de perfis e no relatório final, sem
  permitir que saúde local seja interpretada como publicação LAN.

## 2026-08-02 - ADR-REF-01 aceita para o piloto Nexo–Compras

- Decision: o piloto utilizará `RFP-NC-01` em `D2–D3/A1/shadow`.
- Action: implementar `WP-REF-00`, começando pelos schemas e exemplos em
  `contracts/reflexivity/1.0.0` — concluída.
- Decision: o gate de `WP-REF-00` foi aprovado após validação reproduzível de
  schemas, referências, exemplos positivos e exemplos negativos.
- Evidence: `./scripts/contracts/validate-reflexivity.sh` confirma que
  `D2–D3/A1/shadow` não possui efeito operacional nem ação corretiva.
- Impediment: `REF-01` depende de `EXEC-01`, `PROV-01`, `INF-01` e `SGE-01`.
- Authority boundary: nenhum efeito operacional ou ação corretiva está
  autorizado.

## 2026-08-02 - Início de EXEC-01

- Decision: `IntegrationRun` é o próximo objeto funcional a ser materializado,
  antes de `REF-01`.
- Action: iniciar `WP-EXEC-01` pela validação do contrato
  `contracts/execution/1.0.0`.
- Impediment: persistência e serviço dependem de `PROV-01`, `INF-01` e do
  acordo ativo Nexo–Compras.

## 2026-08-02 - Política de abstração C++

- Decision: o núcleo usará tipos de valor, agregados encapsulados, alternativas
  fechadas e transições puras; polimorfismo virtual fica restrito às portas
  externas com benefício demonstrável.
- Action: aplicar `ADR-CPP-01` em `EXEC-01B/C` antes da implementação do
  serviço ou da persistência.
- Authority boundary: esta decisão não autoriza o `AssessmentEngine` nem
  efeitos operacionais reflexivos.

## 2026-08-02 - Análise vetorial derivada

- Decision: vetores e embeddings são interpretações derivadas; não pertencem
  ao agregado `IntegrationRun` nem substituem validação determinística.
- Action: registrar `ADR-VEC-01`; manter `VEC-LAB-01` posterior a
  `EXEC-01`, `PROV-01` e `INF-01`.
- Authority boundary: nenhuma análise vetorial produz gate, efeito operacional
  ou ação automática no piloto.

## 2026-08-02 - EXEC-01B iniciado

- Decision: o núcleo começa pelos tipos de valor e pelo agregado `IntegrationRun`
  encapsulado, conforme `ADR-CPP-01`.
- Action: materializar `RunId`, referências tipadas, relações fechadas e fábrica
  validada antes da máquina de estados ou infraestrutura.
- Evidence: `sister_core_tests` valida criação válida, estado inicial e rejeição
  de proposta inválida.
- Authority boundary: nenhum serviço, banco, JSON, autorização por acordo,
  análise vetorial ou `AssessmentEngine` entra neste incremento.

## 2026-08-02 - EXEC-01C iniciado

- Decision: execução e validade serão máquinas de estado ortogonais, operadas
  por funções puras e resultados tipados.
- Action: implementar transições de autorização, início, conclusão, falha,
  cancelamento, supersessão e marcação de validade.
- Evidence: `sister_core_tests` valida o ciclo proposto → autorizado → running
  → completed e mantém validade `pending` até transição explícita.
- Authority boundary: nenhuma transição consulta infraestrutura ou concede
  autoridade operacional.

## 2026-08-02 - EXEC-01C concluído

- Decision: a matriz de execução e validade foi fechada sem dependências de
  infraestrutura.
- Evidence: build Release, 19 testes executados/aprovados, 7 skips condicionais
  explicitamente contabilizados, validador de contrato e validação de
  governança aprovados.
- Result: `EXEC-01C` concluído; `EXEC-01D`, `EXEC-01E` e `EXEC-01F` permanecem
  não iniciados.

## 2026-08-02 - FED-01 iniciado

- Decision: a fundação federativa será materializada antes de ligar
  `IntegrationRun` à infraestrutura.
- Action: fortalecer o registro em memória com identidade, versões, capacidades
  versionadas e estados operacional/maturidade independentes.
- Authority boundary: `FED-01` não cria acordos, autoriza execuções nem inicia
  persistência ou HTTP.

## 2026-08-02 - FED-01 concluído

- Decision: o registro federativo aceita identidade e capacidades declaradas,
  mas não concede autorização de consumo ou execução.
- Evidence: tipos fortes, capacidades versionadas, estados independentes,
  registro idempotente, conflitos rejeitados, contrato 1.0.0 e testes aprovados.
- Result: `FED-01` concluído; `AGR-01` é o próximo cartão.

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

## 2026-08-02 - Propriedade do processo de desenvolvimento

- Decision: um PID isolado não autoriza sinalização; o registro de processo
  inclui UID, ambiente, executável e instante de início do kernel.
- Decision: `stop.sh` falha fechado diante de PID file legado, inseguro,
  adulterado ou associado a outro processo, usuário ou worktree.
- Decision: falha de parada bloqueia `serve.sh` e `run_all.sh`; somente ausência
  comprovada ou encerramento confirmado permite continuar.

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
