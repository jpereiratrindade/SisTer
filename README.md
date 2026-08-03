# SisTer

SisTer e um teste de plataforma federativa de convergencia territorial orientada por contratos.

```text
SisTer nao integra sistemas porque controla seus codigos.
SisTer integra sistemas porque reconhece contratos comuns.
```

## Hipotese

O centro do projeto e `contracts/`, nao `apps/`. Sistemas como MorfoCampo,
DroneOps, CampoNode, Radar-Sister Resiliencia e Sister-Clima podem manter
autonomia operacional e interface propria, desde que entreguem contratos
comuns, evidencias e proveniencia verificavel.

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
./scripts/run_all.sh --profile dev-ecosystem
```

Os perfis separam afirmações que não são equivalentes:

```bash
./scripts/run_all.sh --profile dev-core       # núcleo, sisterd e smoke
./scripts/run_all.sh --profile dev-ecosystem  # inclui subsistemas opcionais
./scripts/run_all.sh --profile dev-ecosystem-strict # qualquer degradação bloqueia
./scripts/run_all.sh --profile sec-03v        # pré-requisitos estritos, não fecha o gate
```

A preparação privilegiada do host candidato e o preflight fail-closed estão
descritos em [`docs/operations/SEC-03V-ENV.md`](docs/operations/SEC-03V-ENV.md).

`dev-ecosystem` sobe o núcleo e tenta garantir os subsistemas declarados com
`ensure-running`. Falha opcional produz `PASS_WITH_DEGRADATION`; falha de um
componente exigido pelo perfil produz `BLOCKED` e código `2`. Cada subsistema
continua podendo ser executado isoladamente, mas nenhum deles inicia o SisTer.
`quality.json` permanece evidência exclusiva da qualidade da árvore;
`run-all-status.json` registra banco, prontidão, smoke e ecossistema.
O ciclo local usa um registro de processo `0600` e somente encerra o PID após
validar UID, ambiente, executável do worktree e instante de início em `/proc`.

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

No perfil `dev-ecosystem`, o SisTer também verifica os subsistemas contratados
declarados com `ensure-running` em `config/local_resources.json`. Serviços
saudáveis são preservados; os indisponíveis são iniciados pelo comando
governado e seus logs ficam em `.run/subsystems/`. O perfil `dev-core` não
consulta nem inicia subsistemas.

Subsistemas conteinerizados podem declarar `refresh.on-source-change`. O fluxo
comum apenas informa divergência; não executa atualização ou rebuild implícito.
Para solicitar explicitamente a reconciliação, use `--update-subsystems` com o
perfil de ecossistema. Bancos e outros dados persistentes permanecem nos
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
http://<ip-da-maquina>:8000
http://localhost:8000/login
http://localhost:8000/api/health
http://localhost:8000/api/systems
http://localhost:8000/api/contracts
http://localhost:8000/api/evidence
http://localhost:8000/api/diagnostics
http://localhost:8000/api/integrations/sister-studio
```

Somente `health` e a home institucional sao publicos. `systems` e o JavaScript
do painel exigem uma sessao identificada. `contracts`, `evidence`,
`diagnostics` e a integração com o Sister-Studio exigem sessao com papel
`admin`.

Rotas sensíveis são autorizadas por capacidade e falham fechadas quando não há
política declarada. Integrações Clima e Nexo exigem, respectivamente,
`climate.dashboard.read` e `nexo.projects.read`; administração de identidades
exige `identity.users.manage`, e evidências de maturidade exigem
`maturity.evidence.read`. Consulte a
[ADR-0016](docs/adr/ADR-0016-capability-based-authorization.md).

O SEC-02V validou e a `v0.2.7` publica a identidade interna Ed25519 para uma
única política: `GET /integrations/nexo/projects` é encaminhada como
`GET /api/v1/projects`, com uso interno, read-only e shadow. O cliente não
encaminha cookie nem identidade externa e o Nexo valida audiência, capacidade,
finalidade, tempo, assinatura e `jti`. Replay depois de reinício continua como
risco residual; escrita e produção externa permanecem bloqueadas. Consulte a
[evidência SEC-02V](docs/evidence/security/SEC-02V.md).

O adaptador Sister-Studio usa TLS verificado e segredo de execução. A
configuração e a fronteira de dados estão em
`adapters/sister_studio/README.md`; conteúdo de usuários não é compartilhado
na fase inicial.

O Sister-Clima e reconhecido pelo manifesto
`examples/sister_clima_manifest_example.json` e aparece somente no catalogo
autenticado, com acesso controlado a sua aplicacao local. A fronteira de
compartilhamento e as limitacoes da importacao por arquivo estao em
`adapters/sister_clima/README.md`.
O uso por pessoas identificadas em pesquisa publica sem finalidade comercial e
regido por `sister-clima.governance/1.0.0`; detalhes, atribuicoes e gatilhos de
revisao estao em `docs/governance/SISTER_CLIMA_DATA.md`.

Em desenvolvimento, o primeiro acesso a `/login` pode criar a conta
administradora inicial. Em produção, o bootstrap HTTP permanece desativado e o
administrador deve ser criado localmente, sob o usuário do serviço:

```bash
sudo -u sister env SISTER_AUTH_FILE=/var/lib/sister/auth-users.tsv \
  /opt/sister/build/apps/sisterctl/sisterctl \
  auth bootstrap-admin "Administrador SisTer" admin@example.org
```

Depois do login, a barra lateral libera as visoes internas e a opção **Equipe**,
em `/admin/users`, permite cadastrar as demais contas. Consulte a
[ADR-0017](docs/adr/ADR-0017-offline-administrator-bootstrap.md).

Durante a migração de desenvolvimento, uma conta ativa do Sister-Studio pode
se tornar a identidade inicial do SisTer sem perder seu UUID, autoria ou
arquivos. A senha anterior não é copiada: uma nova senha é solicitada com
entrada oculta diretamente no terminal.

```bash
./scripts/auth/import_studio_user.sh --reset usuario@example.org
```

O modo `--reset` preserva o cadastro anterior do SisTer em um backup local
recuperável, importa somente a identidade selecionada e reinicia o `sisterd`.
Depois disso, o SisTer passa a ser a autoridade de login e o Studio reutiliza
essa sessão.

O comando interno `sisterctl auth-import-user` é reservado a migração,
manutenção local ou break-glass. Não deve ser executado concorrentemente com o
`sisterd`; o procedimento operacional deve incluir backup e rollback.

As senhas sao derivadas com PBKDF2-HMAC-SHA256 e sal aleatorio. As identidades
persistem em `.run/auth-users.tsv`, com permissao exclusiva do usuario do
processo. As sessões persistem em `.run/auth-users.tsv.sessions` somente pelo
hash SHA-256 do token, nunca pelo token bruto, e expiram em oito horas.
Para usar outro caminho no desenvolvimento com TCP loopback explícito:

```bash
SISTER_AUTH_FILE=/caminho/protegido/auth-users.tsv \
SISTER_ENV=development \
SISTER_WORKERS=4 \
SISTER_BIND_HOST=127.0.0.1 \
SISTER_ENABLE_HTTP_BOOTSTRAP=false \
SISTER_ENABLE_LEGACY_PROXY=false \
SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY=false \
SISTER_ENABLE_NEXO_SIGNED_INTEGRATION=false \
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
- `SISTER_ENABLE_NEXO_SIGNED_INTEGRATION`: Habilita exclusivamente a leitura
  shadow assinada de projetos do Nexo (padrão `false`); é independente dos
  proxies legados e exige a chave e o `kid` válidos antes do listener.
- `SISTER_NEXO_PORT`: Porta para o serviço de federação Nexo (padrão `8015`).
- `SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE`: Caminho absoluto da chave privada
  Ed25519 usada nas asserções internas do Nexo; o arquivo deve ser `0600`.
- `SISTER_INTERNAL_IDENTITY_KEY_ID`: Identificador `kid` da chave ativa.
- `SISTER_INTERNAL_IDENTITY_TTL_SECONDS`: Validade da asserção interna, entre 1
  e 300 segundos (padrão `60`).
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
./build/apps/sisterctl/sisterctl validate-manifest examples/morfocampo_manifest_example.json
./build/apps/sisterctl/sisterctl validate-manifest examples/sister_clima_manifest_example.json
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

Cada sistema federado tambem declara no seu contrato o que compartilha com o SisTer, o que permanece nativo de sua propria plataforma, o link de acesso direto e a classificacao publico/restrito/privado/sensivel. A integracao segue a cadeia dado, informacao, conhecimento e sabedoria: a informacao ofertada pelo sistema produtor chega ao SisTer como dado contratado; depois de validada e contextualizada, pode virar informacao integrada, conhecimento territorial e apoio decisorio governado.

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
