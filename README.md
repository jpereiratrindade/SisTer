
<!-- SISTER-INFRA-BOUNDARY:BEGIN -->
> [!IMPORTANT]
> **Fronteira operacional:** a exposição HTTPS/LAN do ecossistema, o HAProxy,
> o TLS de borda e a execução conjunta de SisTer + Nexo pertencem ao repositório
> **Sister-Infra**. Este repositório continua responsável pelo núcleo SisTer,
> seus contratos, governança, persistência, qualidade e execução isolada.

## Execução e infraestrutura do ecossistema

Para desenvolver ou validar somente o núcleo SisTer:

```bash
./scripts/run_all.sh --profile dev-core
```

Para levantar SisTer + Nexo + gateway único em laboratório LAN, use o repositório
irmão `sister-infra`:

```bash
cd ../sister-infra
./bin/sister-infra up --profile lan
./bin/sister-infra verify --profile lan
```

Os scripts de gateway mantidos neste repositório permanecem temporariamente como
**legado de transição**, para reprodução de baselines e testes históricos. Novas
automações de exposição, TLS, preparação de clientes LAN e promoção operacional
devem ser implementadas em `Sister-Infra`, não no núcleo SisTer.

Repositório público de referência:
`git@github.com:jpereiratrindade/Sister-Infra.git`.
<!-- SISTER-INFRA-BOUNDARY:END -->

<!-- SISTER-PORTAL:START -->

<div align="center">

# SisTer

## Sistema Inteligente e Resiliência de Sistemas e Ecossistemas

**Pesquisa, engenharia e software para construir, integrar, observar e evoluir ecossistemas compostos por subsistemas autônomos.**

### [Acessar o Portal do SisTer](https://jpereiratrindade.github.io/SisTer/)

[![Portal](https://img.shields.io/badge/Portal-SisTer-174a72?style=for-the-badge)](https://jpereiratrindade.github.io/SisTer/)
[![GitHub](https://img.shields.io/badge/Código-GitHub-24292f?style=for-the-badge&logo=github)](https://github.com/jpereiratrindade/SisTer)
[![GitLab](https://img.shields.io/badge-Espelho-GitLab-fc6d26?style=for-the-badge&logo=gitlab)](https://gitlab.com/jpereiratrindade/sister)
[![Licença](https://img.shields.io/badge/Licença-GPL--3.0--or--later-174a72?style=for-the-badge)](LICENSE)

</div>

---

## Visão geral

O **SisTer** é uma plataforma para construção e operação de ecossistemas de software formados por subsistemas autônomos.

O projeto organiza a integração desses subsistemas por meio de:

- contratos explícitos;
- capacidades registradas;
- fronteiras controladas;
- evidências rastreáveis;
- avaliação da operação;
- decisões autorizadas de engenharia;
- experimentos executáveis;
- reflexão sobre o comportamento do próprio ecossistema.

O SisTer reúne pesquisa, arquitetura e implementação em uma mesma trajetória de desenvolvimento. Hipóteses são materializadas em software, executadas em condições controladas, observadas e avaliadas. As distinções validadas passam a compor o domínio, a arquitetura, os contratos, os testes e o conhecimento operacional do sistema.

## Comece por aqui

| Recurso | Conteúdo |
|---|---|
| **[Portal do SisTer](https://jpereiratrindade.github.io/SisTer/)** | Visão geral, método, Harness, grafos, experimentos e validação |
| **[Código no GitHub](https://github.com/jpereiratrindade/SisTer)** | Repositório principal de desenvolvimento |
| **[Espelho no GitLab](https://gitlab.com/jpereiratrindade/sister)** | Espelho do projeto e pipeline GitLab Pages |
| **[Documento completo](https://jpereiratrindade.github.io/SisTer/documentos/engenharia_ontologica_experimental_sister_v1_0.pdf)** | Engenharia Ontológica Experimental aplicada ao SisTer |
| **[Licença](LICENSE)** | GNU General Public License v3 ou posterior |

## Elementos centrais

| Elemento | Função no SisTer |
|---|---|
| **Subsistemas** | Implementam capacidades próprias e preservam sua autonomia |
| **Contratos** | Definem finalidade, participantes, responsabilidades, estados e evidências |
| **Gateway** | Organiza a exposição e o acesso aos componentes do ecossistema |
| **Centro de Engenharia** | Apoia avaliação, autorização e evolução da arquitetura |
| **Harness experimental** | Executa hipóteses e produz observações controladas |
| **Reflexividade** | Relaciona propósito, comportamento esperado e operação observada |
| **Grafos** | Representam relações entre entidades, capacidades, contratos e evidências |

## Tecnologia e desenvolvimento

O SisTer adota:

- C++ como linguagem principal;
- interfaces web para interação e observação;
- integração por contratos;
- arquitetura modular;
- rastreabilidade de decisões e evidências;
- execução local e controlada;
- software livre sob a licença GPLv3.

<!-- SISTER-PORTAL:END -->


---

## Documentação anterior do projeto

# SisTer

SisTer e um teste de plataforma federativa de convergencia territorial orientada por contratos.

```text
SisTer nao integra sistemas porque controla seus codigos.
SisTer integra sistemas porque reconhece contratos comuns.
```

## Hipotese

O centro do projeto e `contracts/`, nao `apps/`. Nesta fase, somente o
`sister_reference` participa da validacao operacional. Integracoes reais ficam
em quarentena ate demonstrarem conformidade com os contratos, evidencias e
fronteiras da plataforma.

## Base tecnica

- C++20 como padrao inicial.
- CMake para build.
- `sister_core` como biblioteca de dominio.
- `sisterctl` como CLI minima para validar manifestos.
- `web/` como primeira interface estatica de convergencia e inspecao.
- PostgreSQL como banco operacional planejado.
- pgvector para analises vetoriais, similaridade semantica e recuperacao de conhecimento.
- Contratos JSON Schema em `contracts/`.
- Governanca inspirada na estrutura usada em `LabGestao/docs`.

C++20 e uma escolha conservadora e portavel. C++23 pode ser adotado depois em modulos isolados se houver ganho real com `std::expected`, ranges mais completos ou melhorias de biblioteca aceitas pelo toolchain alvo.

## Build

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## Ponto de entrada do ecossistema

O SisTer é o orquestrador raiz do ambiente integrado. Para desenvolver catálogo,
autenticação federada e navegação entre sistemas, inicie sempre neste
repositório:

```bash
./scripts/run_all.sh --profile dev-reference
```

Os perfis separam afirmações que não são equivalentes:

```bash
./scripts/run_all.sh --profile dev-core       # núcleo, sisterd e smoke
./scripts/run_all.sh --profile dev-reference  # núcleo + referência obrigatória
./scripts/run_all.sh --profile dev-lan        # referência via gateway federador
./scripts/run_all.sh --profile test-core      # núcleo isolado no worktree de teste
./scripts/run_all.sh --profile sec-03v        # pré-requisitos estritos, não fecha o gate
```

A preparação privilegiada do host candidato e o preflight fail-closed estão
descritos em [`docs/operations/SEC-03V-ENV.md`](docs/operations/SEC-03V-ENV.md).

`dev-reference`, `dev-lan` e `sec-03v` garantem exclusivamente o
`sister_reference`. Integrações reais permanecem em quarentena e não são
iniciadas, roteadas ou usadas como evidência do núcleo. Falha da referência
produz `BLOCKED` e código `2`.
`quality.json` permanece evidência exclusiva da qualidade da árvore;
`run-all-status.json` registra banco, prontidão, smoke e ecossistema.
O ciclo local usa um registro de processo `0600` e somente encerra o PID após
validar UID, ambiente, executável do worktree e instante de início em `/proc`.

Cada resultado declara sua superfície operacional. `dev-core` e
`dev-reference` são `LOCAL_ONLY`, mantêm o núcleo em loopback e registram
`Public gateway: NOT_REQUESTED`. `dev-lan` é `LAN_FEDERATED`: mantém o núcleo
em socket Unix e publica somente o HAProxy em `8443`. O manifesto privado em
`.run/executions/` distingue processos e contêineres iniciados pela execução
daqueles que já existiam; o teardown encerra somente os recursos próprios.

Para encerrar a execução governada do ambiente de desenvolvimento:

```bash
./scripts/app/stop.sh dev
```

Em `dev-lan`, `./scripts/stop_gateway_lan_lab.sh` detecta o manifesto ativo e
delega ao mesmo lifecycle, encerrando também a referência iniciada pela execução.

## Produção

O `sisterd` é um plano de controle interno, não uma borda HTTP pública. Em
produção ele deve ficar atrás de um gateway/reverse proxy especializado, que
termina TLS e trata HTTP, WebSocket, limites e observabilidade. O processo
exige o socket Unix ativado pelo systemd, recusa qualquer listener TCP e recusa
os proxies legados. Consulte as ADRs
[0015](docs/adr/ADR-0015-sisterd-transport-quarantine.md) e
[0021](docs/adr/ADR-0021-local-upstream-unix-socket-activation.md).

A baseline `v0.2.5` concluiu SEC-00, SEC-01, SEC-01A e SEC-01B: quarentena de
transporte, autorização por capacidades sem fallback de papel e bootstrap
administrativo offline sem emissão de sessão. A `v0.2.6` acrescentou SEC-01C e
SEC-01D sem alterar tags anteriores. A `v0.2.7` incorpora SEC-02 sob autorização
estrita: uma única leitura interna em modo shadow. Gateway e gates operacionais
continuam pendentes; nenhuma dessas baselines declara o sistema pronto para
exposição externa. Consulte a
[baseline de segurança](docs/architecture/SISTERD_SECURITY_BASELINE.md).

Na revisão posterior, SEC-01C contém exceções do parser e dos workers, enquanto
SEC-01D aplica limites independentes por endereço observado, identidade,
combinação e processo. Rejeições de login retornam `429` com `Retry-After`. O
servidor ignora `X-Forwarded-For` para essa decisão até existir uma relação de
confiança formalizada com o gateway. Esses controles são fechados na release
`v0.2.6`; a tag `v0.2.5` permanece imutável. Consulte a
[ADR-0019](docs/adr/ADR-0019-http-robustness-and-login-rate-limiting.md).

A EFE-SisTer/1.4 é a referência funcional e de engenharia corrente e exige
segurança orientada por ameaças, controles e evidências. A EFE-SisTer/1.2
permanece como referência histórica de alinhamento de segurança. A `v0.2.6` publicou o
MAES-SisTer/1.0 junto ao fechamento de SEC-01C/01D. O SEC-02V aprovou o candidato
posterior e o SEC-02M converteu os limites aprovados em configuração e rota
executáveis para a `v0.2.7`. Consulte o
[alinhamento normativo](docs/architecture/EFE_SISTER_1_2_ALIGNMENT.md).

SEC-03A define o gateway especializado como HAProxy Community 3.2 LTS e fixa
um [perfil executável da fronteira](docs/security/GATEWAY_SECURITY_PROFILE.md).
Esse perfil ainda não representa implantação nem autoriza exposição externa.
SEC-03B foi encerrado como `LAB_PROVEN_WITH_RESTRICTIONS` por decisão explícita:
normalização segura de `Content-Length`, remoção de Upgrade isolado e exceção
restrita para Host idêntico duplicado. A
[evidência SEC-03C](docs/evidence/security/SEC-03C.md) encerra a contenção de
abuso em laboratório. A [evidência ISO-01](docs/evidence/security/ISO-01.md)
removeu o listener TCP produtivo. O gate `SEC-03V` foi executado sem skips no
ambiente candidato; consulte a [evidência integral](docs/evidence/security/SEC-03V.md).
O merge controlado foi consolidado na baseline integrada `v0.2.10`. As tags
`v0.2.8` e `v0.2.9` preservam, respectivamente, os contratos de reflexividade
e o contrato `EXEC-01A` como marcos históricos. Consulte o
[registro de baseline](docs/releases/REL-BASE-01.md).

Para preparar um ambiente candidato a produção (Infrastructure as Code),
utilize os scripts de deploy e configurações fornecidos:

- **Unidades:** Instale `ops/systemd/sisterd.service` e `sisterd.socket`, além de
  `ops/tmpfiles.d/sister.conf`; habilite `sisterd.socket`.
- **Credenciais:** Copie `.env.production.example` para `/etc/sister/sister.env` (proteja com `chmod 600`).
- **Deploy:** O script `scripts/app/deploy.sh` centraliza os passos de build (Release), migrações e restart do serviço, dispensando containers de banco embutidos que o modo `dev` exige.


## Servidor/API

O servidor `sisterd` pode ser iniciado diretamente para diagnóstico de baixo
nível:

```bash
./build/apps/sisterd/sisterd 8000 web
```

No perfil `dev-reference`, o SisTer verifica e inicia exclusivamente o
`sister_reference`, declarado com `ensure-running` em
`config/local_resources.json`. Servicos saudaveis sao preservados; processos iniciados
pelo comando ficam registrados em `.run/executions/`. O perfil `dev-core` nao
consulta nem inicia subsistemas.

Subsistemas conteinerizados podem declarar `refresh.on-source-change`. O fluxo
comum apenas informa divergência; não executa atualização ou rebuild implícito.
Para solicitar explicitamente a reconciliação, use `--update-subsystems` com um
perfil que selecione a referência. Bancos e outros dados persistentes permanecem nos
volumes exclusivos declarados pelo subsistema.

O fluxo `dev` deve ser executado no worktree principal. Para preparar e executar
um teste reproduzivel a partir do mesmo local:

```bash
./scripts/test/run.sh head
./scripts/test/run.sh release
```

`head` exige que as alteracoes estejam commitadas e testa o `HEAD` atual.
`release` atualiza as tags a partir de `origin` e testa a tag `v*` mais recente.
O comando sincroniza o worktree `../SisTer-test` e executa nele o fluxo `test`,
usando a porta HTTP `8001` por padrao.

Acesse:

```text
http://localhost:8000
http://localhost:8000/login
http://localhost:8000/api/health
http://localhost:8000/api/systems
http://localhost:8000/api/contracts
http://localhost:8000/api/evidence
http://localhost:8000/api/diagnostics
http://localhost:8000/api/integrations/sister-reference
```

A porta `8000` e interna e permanece em loopback. Acesso por IP da maquina
existe somente no perfil `dev-lan`, pelo gateway HTTPS em `8443`.

Somente `health` e a home institucional sao publicos. `systems` e o JavaScript
do painel exigem uma sessao identificada. `contracts`, `evidence`,
`diagnostics` e os metadados da referencia exigem sessao com papel `admin`.

Rotas sensiveis sao autorizadas por capacidade e falham fechadas quando nao ha
politica declarada. A referencia usa `reference.identity.read` e
`reference.echo.execute`; administracao de identidades exige
`identity.users.manage`, e evidencias de maturidade exigem
`maturity.evidence.read`. Integracoes reais nao sao roteadas nem apresentadas
no catalogo vigente. Consulte a [ADR-0022](docs/adr/ADR-0022-reference-subsystem-validation-boundary.md).

### Identidade local e bootstrap administrativo

As execuções gerenciadas por `run_all.sh` usam PostgreSQL como backend de
autenticação humana. Identidades ficam em `sister_users` e sessões opacas em
`sister_sessions`; reiniciar o SisTer ou trocar `dev-reference` por `dev-lan`
não recria essas estruturas nem perde usuários.

O backend é explícito por `SISTER_AUTH_BACKEND=postgresql`. O armazenamento
legado por arquivo permanece disponível somente quando `SISTER_AUTH_BACKEND=file`
é selecionado, principalmente para testes isolados e procedimentos compatíveis.
O perfil `dev-lan` não gera nem consome `.run/gateway/auth-users.tsv`.

O bootstrap HTTP permanece desativado no perfil `dev-lan`. Em uma instalação
sem administrador, pare o gateway LAN e crie explicitamente a primeira conta:

```bash
./scripts/stop_gateway_lan_lab.sh
./scripts/bootstrap_gateway_lan_admin.sh \
  "Administrador SisTer" jose.pereira-trindade@embrapa.br
```

O comando solicita a senha de forma oculta e grava o administrador diretamente
em `sister_users`. O `sisterd` autentica esse usuário no PostgreSQL, sem etapa de
sincronização para arquivo intermediário.

A administração persistente de usuários locais pode ser feita pelo terminal:

```bash
./scripts/auth/userctl.sh --environment dev list

./scripts/auth/userctl.sh --environment dev \
  create email@exemplo.org "Nome do usuário" admin

./scripts/auth/userctl.sh --environment dev password email@exemplo.org
./scripts/auth/userctl.sh --environment dev role email@exemplo.org admin
./scripts/auth/userctl.sh --environment dev activate email@exemplo.org
./scripts/auth/userctl.sh --environment dev deactivate email@exemplo.org
```

As senhas são derivadas com PBKDF2-HMAC-SHA256, sal aleatório e 210000
iterações. Tokens de sessão são armazenados somente pelo hash SHA-256 em
`sister_sessions`, com expiração de oito horas e revogação explícita no logout.
A execução normal do SisTer não cria, apaga nem redefine credenciais; o
bootstrap inicial é uma operação administrativa explícita.

O procedimento de certificado, `/etc/hosts`, proxy, acesso LAN e login está em
[`docs/operations/GATEWAY_LAN_LAB.md`](docs/operations/GATEWAY_LAN_LAB.md).

Para usar outro caminho no desenvolvimento com TCP loopback explícito:

```bash
SISTER_AUTH_FILE=/caminho/protegido/auth-users.tsv \
SISTER_ENV=development \
SISTER_WORKERS=4 \
SISTER_BIND_HOST=127.0.0.1 \
SISTER_ENABLE_HTTP_BOOTSTRAP=false \
SISTER_ENABLE_LEGACY_PROXY=false \
SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY=false \
SISTER_ENABLE_REFERENCE_SUBSYSTEM=false \
  ./build/apps/sisterd/sisterd 8000 web
```

Produção não aceita esse comando: recebe o socket Unix exclusivamente por
`sisterd.socket`, conforme ADR-0021.

O `sisterd` suporta diversas variáveis de ambiente para configuração avançada:
- `SISTER_ENV`: Define o ambiente (`development` ou `production`, padrão `production`).
- `SISTER_WORKERS`: Número de threads (padrão baseado em hardware, máx 16).
- `SISTER_QUEUE_LIMIT`: Limite da fila de conexões simultâneas (padrão `256`).
- `SISTER_BIND_HOST`: Host de rede para o bind (padrão `127.0.0.1`).
- `SISTER_ENABLE_HTTP_BOOTSTRAP`: Cadastro inicial pela API HTTP (padrão `false` em produção; não pode ser habilitado em produção).
- `SISTER_ENABLE_LEGACY_PROXY`: Proxy HTTP embarcado, permitido somente para laboratório (padrão `false`).
- `SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY`: Túnel WebSocket embarcado, permitido somente para laboratório (padrão `false`).
- `SISTER_ENABLE_REFERENCE_SUBSYSTEM`: habilita somente a referencia normativa
  (padrao `false`).
- `SISTER_REFERENCE_PORT`: porta loopback da referencia (padrao `19001`).
- `SISTER_INTERNAL_PROXY_TOKEN`: segredo efemero exigido quando a referencia
  esta habilitada; `run_all.sh` gera um valor novo para cada execucao.
- `SISTER_COOKIE_SECURE`, `SISTER_HSTS`, `SISTER_REQUIRE_SAME_ORIGIN`: Controles de segurança (ativos por padrão em `production`).

Os dados territoriais (objetos geoespaciais) ainda são demonstrativos. Sistemas,
contratos, evidências e diagnósticos são lidos do PostgreSQL quando
`SISTER_DATABASE_URL` está definido; sem banco, o servidor usa literais de
fallback sem interrupção de serviço.

## Banco de dados

Subir PostgreSQL com pgvector no ambiente de desenvolvimento:

```bash
cp .env.example .env
# edite SISTER_DB_PASSWORD no .env se necessário
./scripts/db/up.sh dev
# As variáveis de conexão e porta são gerenciadas dinamicamente
# pelo script, usando SISTER_DB_PORT.
```

O banco de desenvolvimento usa o container `sister-dev-db` e volume
persistente `sister_dev_pgdata`. As portas são configuráveis dinamicamente.

Se a porta padrão estiver ocupada, configure uma alternativa sem editar os
scripts:

```bash
SISTER_DEV_DB_PORT=<sua_porta_alternativa> ./scripts/run_all.sh dev
```

Parar o banco sem remover dados:

```bash
./scripts/db/down.sh dev
```

Remover container e volume do ambiente de teste:

```bash
./scripts/db/destroy.sh test
```

Verificar conexão e extensões:

```bash
./scripts/db/check.sh dev
```

Aplicar ou reaplicar a migration inicial:

```bash
./scripts/db/migrate.sh dev
```

Para criar um espaco separado de teste:

```bash
./scripts/test/create_worktree.sh
./scripts/test/run.sh head
```

Detalhes: `docs/architecture/ENVIRONMENTS.md`.

## Validar um manifesto

```bash
python3 tests/reference_subsystem_contract_test.py
```

## Interface

A primeira interface e estatica e pode ser aberta diretamente:

```text
web/index.html
```

Ou servida localmente:

```bash
python3 -m http.server 8000 -d web
```

Depois acesse:

```text
http://localhost:8000
```

Ela apresenta uma visao operacional dos sistemas federados, contratos de integracao, evidencias, proveniencia e um mapa territorial sintetico para validar o conceito de convergencia.

A identidade visual inicial segue a linha do `Radar-Sister Resiliencia`: topo horizontal institucional, azul como cor estrutural, acentos teal, cards brancos, metricas compactas, dashboard de resultados e rodape com referencias explicitas a governanca, LGPD e seguranca.

### Funcionalidades de produto

1. `Integracao e transformacao de conhecimento`
   Responsavel por ingerir contratos, validar pacotes, transformar dados federados em objetos territoriais e registrar conhecimento produzido pela integracao.

2. `Sintese tecnica e diagnostico dos servicos`
   Responsavel por dar transparencia ao estado dos servicos que sustentam as entregas do SisTer, incluindo prontidao, conformidade, riscos operacionais e sinais de governanca.

Essa separacao evita misturar a funcao epistemica do SisTer, que transforma conhecimento territorial, com a funcao operacional de gestao e transparencia da plataforma.

Cada subsistema candidato declara no contrato o que compartilha com o SisTer,
o que permanece nativo e sua classificacao
publico/restrito/privado/sensivel. Acesso operacional externo nunca e direto:
depende de promocao propria e mediacao pelo gateway SisTer.

## SGE e maturidade

Para executar todos os testes disponíveis localmente e publicar as avaliações
de maturidade dos componentes resolvíveis:

```bash
./scripts/sge verify
```

O comando executa a suíte geral de qualidade e depois `maturity publish-all`.
Componentes externos sem raiz local configurada aparecem como `SKIP`, sem
ocultar os testes que efetivamente foram executados.

Para publicar somente uma avaliação de maturidade:

```bash
./scripts/sge maturity publish pre-alpha
```

Comandos principais:

```bash
./scripts/sge maturity evaluate pre-alpha
./scripts/sge maturity evaluate pre-alpha --engine compare
./scripts/sge maturity publish pre-alpha
./scripts/sge maturity publish-all pre-alpha
./scripts/sge maturity publish pre-alpha --engine declarative
./scripts/sge maturity validate
./scripts/sge maturity validate --status-json .run/maturity/latest.json
```

O tutorial completo de uso fica em `engineering/maturity/README.md`.
A arquitetura de engines e governanca fica em `docs/architecture/sgr/`.
No painel, a aba `Testes Disponíveis` mostra o catálogo de checks declarados
nos perfis; a aba `Evidências Executadas` mostra somente o que rodou na última
atestação publicada.

## Documentacao

- `docs/CONCEPTUAL_BASE.md`: conexao viva com a construcao conceitual e ontologica mantida em `docs/conceptual`.
- `docs/architecture/ENVIRONMENTS.md`: separacao entre desenvolvimento, teste, containers e worktree.
- `docs/architecture/DDD.md`: modelo de dominio e contextos delimitados.
- `docs/architecture/INTERFACE.md`: interface, navegacao, identidade visual e proximos incrementos.
- `docs/architecture/DATABASE.md`: arquitetura PostgreSQL e pgvector.
- `docs/architecture/CONTAINERS.md`: estrategia de containers e persistencia do banco.
- `docs/architecture/sgr/`: arquitetura do SGR, engines de verificacao e modos de governanca.
- `engineering/maturity/README.md`: tutorial de uso do modulo de maturidade do SGE.
- `docs/governance/PUBLIC_PRIVATE_SCOPE.md`: escopo publico, restrito e privado.
- `docs/adr/`: decisoes arquiteturais aceitas.
- `docs/dai/DAI.md`: decisoes, acoes e impedimentos.
- `docs/governance/README.md`: base de governanca operacional.
- `docs/governance/INTEGRATED_PROJECTS.md`: coordenacao de portas, containers,
  volumes e outros recursos entre repositorios.
- `config/local_resources.json`: registro central, legivel por maquina, dos
  recursos reservados no ambiente local.

## Qualidade e governanca

```bash
./scripts/sge verify
```

Para executar apenas build, CTest e validadores do repositório, sem publicar
maturidade:

```bash
./scripts/run_quality.sh
```

## Licença

Este projeto é distribuído sob os termos da GNU General Public License versão 3 ou posterior (`GPL-3.0-or-later`). Consulte o arquivo [LICENSE](LICENSE).
