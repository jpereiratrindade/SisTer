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
./scripts/run_all.sh dev 8000
```

O comando sobe o núcleo do SisTer e garante os subsistemas declarados com
`ensure-running`. Cada subsistema continua podendo ser executado isoladamente
em seu próprio repositório, mas nenhum deles inicia o SisTer.

## Produção

Para colocar o SisTer em produção (Infrastructure as Code), utilize os scripts de deploy e configurações do sistema fornecidos:

- **Template do Serviço:** Copie `ops/systemd/sisterd.service` para `/etc/systemd/system/sisterd.service`.
- **Credenciais:** Copie `.env.production.example` para `/etc/sister/sister.env` (proteja com `chmod 600`).
- **Deploy:** O script `scripts/app/deploy.sh` centraliza os passos de build (Release), migrações e restart do serviço, dispensando containers de banco embutidos que o modo `dev` exige.


## Servidor/API

O servidor `sisterd` pode ser iniciado diretamente para diagnóstico de baixo
nível:

```bash
./build/apps/sisterd/sisterd 8000 web
```

No fluxo `dev`, o SisTer também verifica os subsistemas contratados declarados
com `ensure-running` em `config/local_resources.json`. Serviços saudáveis são
preservados; os indisponíveis são iniciados pelo comando governado e seus logs
ficam em `.run/subsystems/`. Use `SISTER_ENSURE_SUBSYSTEMS=0` para uma subida
isolada ou `SISTER_SUBSYSTEMS_STRICT=1` para falhar diante de qualquer
degradação.

Subsistemas conteinerizados podem declarar `refresh.on-source-change`. Nesse
caso, o fluxo compara o conteúdo das fontes com a última execução bem-sucedida
e reconstrói somente a aplicação quando necessário. Bancos e outros dados
persistentes permanecem nos volumes exclusivos declarados pelo subsistema.

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

No primeiro acesso a `/login`, o SisTer permite criar a conta administradora
inicial. Depois do login, a barra lateral libera as visoes internas e a opcao
**Equipe**, em `/admin/users`, permite cadastrar outras contas como `user` ou
`admin`.

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

As senhas sao derivadas com PBKDF2-HMAC-SHA256 e sal aleatorio. As identidades
persistem em `.run/auth-users.tsv`, com permissao exclusiva do usuario do
processo; os tokens de sessao ficam somente em memoria e expiram em oito horas.
Para usar outro caminho ou configurar o servidor:

```bash
SISTER_AUTH_FILE=/caminho/protegido/auth-users.tsv \
SISTER_ENV=production \
SISTER_WORKERS=4 \
SISTER_BIND_HOST=127.0.0.1 \
  ./build/apps/sisterd/sisterd 8000 web
```

O `sisterd` suporta diversas variáveis de ambiente para configuração avançada:
- `SISTER_ENV`: Define o ambiente (`development` ou `production`, padrão `production`).
- `SISTER_WORKERS`: Número de threads (padrão baseado em hardware, máx 16).
- `SISTER_QUEUE_LIMIT`: Limite da fila de conexões simultâneas (padrão `256`).
- `SISTER_BIND_HOST`: Host de rede para o bind (padrão `127.0.0.1`).
- `SISTER_NEXO_PORT`: Porta para o serviço de federação Nexo (padrão `8015`).
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

## Documentacao

- `docs/CONCEPTUAL_BASE.md`: conexao viva com a construcao conceitual e ontologica mantida em `docs/conceptual`.
- `docs/architecture/ENVIRONMENTS.md`: separacao entre desenvolvimento, teste, containers e worktree.
- `docs/architecture/DDD.md`: modelo de dominio e contextos delimitados.
- `docs/architecture/INTERFACE.md`: interface, navegacao, identidade visual e proximos incrementos.
- `docs/architecture/DATABASE.md`: arquitetura PostgreSQL e pgvector.
- `docs/architecture/CONTAINERS.md`: estrategia de containers e persistencia do banco.
- `docs/architecture/sgr/`: arquitetura do SGR, engines de verificacao e modos de governanca.
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
python3 scripts/validate_governance_repo.py
python3 scripts/validate_tool_contracts.py
./scripts/run_quality.sh
```
