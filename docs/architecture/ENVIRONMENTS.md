# Ambientes de desenvolvimento e teste

## Decisao

O SisTer usa dois espacos de trabalho operacionais:

```text
/run/media/jpereiratrindade/labeco10T/dev/cpp/SisTer
/run/media/jpereiratrindade/labeco10T/dev/cpp/SisTer-test
```

O primeiro e o espaco de desenvolvimento principal. O segundo e um worktree Git
para testes, experimentos, migracoes e validacoes que nao devem contaminar o
estado cotidiano de desenvolvimento.

A base conceitual permanece unica e viva em:

```text
/run/media/jpereiratrindade/labeco10T/dev/Text/SisTer
```

Cada worktree acessa essa base por `docs/conceptual`.

## Containers

O banco roda em container nos dois ambientes. A aplicacao C++ permanece local
durante esta fase para reduzir atrito de compilacao e depuracao.

No Fedora Silverblue, os scripts aceitam dois caminhos:

- com `podman-compose`, `docker-compose` ou `docker compose`, usam `compose.yml`;
- sem Compose, mas com `podman`, constroem a imagem local e executam o banco por
  `podman run`.

O fallback direto por Podman usa a imagem do proprio SisTer, baseada em
`pgvector/pgvector:pg17`.

| Ambiente | Container | Porta host | Volume |
| --- | --- | --- | --- |
| `dev` | `sister-dev-db` | `5432` | `sister_dev_pgdata` |
| `test` | `sister-test-db` | `5433` | `sister_test_pgdata` |

## Criar o worktree de teste

Antes de criar o worktree de teste, o estado que deve ser testado precisa estar
commitado. Isso evita que `SisTer-test` nasca sem scripts, documentos ou
migrations ainda nao registrados no Git.

A partir do repositorio principal:

```bash
./scripts/test/create_worktree.sh
```

Por padrao, o comando cria:

```text
/run/media/jpereiratrindade/labeco10T/dev/cpp/SisTer-test
```

Tambem e possivel informar outro caminho:

```bash
./scripts/test/create_worktree.sh /caminho/para/SisTer-test
```

## Desenvolvimento

No worktree principal:

```bash
./scripts/db/up.sh dev
./scripts/db/migrate.sh dev
./scripts/db/check.sh dev
./scripts/run_quality.sh
```

URL esperada:

```bash
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:5432/sister'
```

## Teste

No worktree de teste:

```bash
./scripts/db/up.sh test
./scripts/db/migrate.sh test
./scripts/db/check.sh test
./scripts/run_quality.sh
```

URL esperada:

```bash
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:5433/sister'
```

## Parar ambientes

Parar sem apagar dados:

```bash
./scripts/db/down.sh dev
./scripts/db/down.sh test
```

Apagar container e volume do ambiente de teste:

```bash
./scripts/db/destroy.sh test
```

O comando `destroy` usa `test` como padrao para evitar remocao acidental do banco
de desenvolvimento.

## Regra de coerencia

Ambientes de teste podem ser descartados e recriados. A coerencia do SisTer nao
deve depender do estado local de um banco de teste, mas de:

- contratos versionados;
- migrations versionadas;
- scripts reproduziveis;
- documentacao governada;
- base conceitual viva conectada;
- rastreabilidade entre decisao, implementacao e evidencia.
