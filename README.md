# SisTer

SisTer e um teste de plataforma federativa de convergencia territorial orientada por contratos.

```text
SisTer nao integra sistemas porque controla seus codigos.
SisTer integra sistemas porque reconhece contratos comuns.
```

## Hipotese

O centro do projeto e `contracts/`, nao `apps/`. Sistemas como MorfoCampo, DroneOps, CampoNode e Radar-Sister Resiliencia podem manter autonomia operacional, interface propria e sincronizacao offline, desde que entreguem contratos comuns, evidencias e proveniencia verificavel.

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

## Servidor/API

O servidor inicial `sisterd` entrega a interface web e endpoints JSON basicos:

```bash
./build/apps/sisterd/sisterd 8000 web
```

Acesse:

```text
http://localhost:8000
http://localhost:8000/api/health
http://localhost:8000/api/systems
http://localhost:8000/api/contracts
http://localhost:8000/api/evidence
http://localhost:8000/api/diagnostics
```

Esta API ainda usa dados demonstrativos em memoria. A ligacao com PostgreSQL sera o proximo incremento.

Enquanto nao houver autenticacao, use o `sisterd` como servidor local/de desenvolvimento.

## Banco de dados

Subir PostgreSQL com pgvector no ambiente de desenvolvimento:

```bash
./scripts/db/up.sh dev
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:5432/sister'
```

O banco de desenvolvimento usa o container `sister-dev-db`, porta `5432` e volume
persistente `sister_dev_pgdata`.

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
cd ../SisTer-test
./scripts/db/up.sh test
./scripts/db/migrate.sh test
```

Detalhes: `docs/architecture/ENVIRONMENTS.md`.

## Validar um manifesto

```bash
./build/apps/sisterctl/sisterctl validate-manifest examples/morfocampo_manifest_example.json
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
- `docs/governance/PUBLIC_PRIVATE_SCOPE.md`: escopo publico, restrito e privado.
- `docs/adr/`: decisoes arquiteturais aceitas.
- `docs/dai/DAI.md`: decisoes, acoes e impedimentos.
- `docs/governance/README.md`: base de governanca operacional.

## Qualidade e governanca

```bash
python3 scripts/validate_governance_repo.py
python3 scripts/validate_tool_contracts.py
./scripts/run_quality.sh
```
