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

O worktree de teste e descartavel e sempre fica em `detached HEAD`. Ele nao e
uma linha paralela de desenvolvimento: seu conteudo deve ser sincronizado a
partir de uma revisao imutavel antes de cada execucao.

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
| `dev` | `sister-dev-db` | `55434` | `sister_dev_pgdata` |
| `test` | `sister-test-db` | `55435` | `sister_test_pgdata` |

Os servidores HTTP tambem usam portas diferentes por padrao:

| Ambiente | Porta HTTP |
| --- | --- |
| `dev` | `8000` |
| `test` | `8001` |

As portas podem ser adaptadas ao host por `SISTER_DEV_DB_PORT`,
`SISTER_TEST_DB_PORT`, `SISTER_DEV_APP_PORT` e `SISTER_TEST_APP_PORT`. Por
exemplo:

```bash
SISTER_DEV_DB_PORT=55440 ./scripts/run_all.sh dev
```

## Criar o worktree de teste

Antes de testar `HEAD`, o estado precisa estar commitado. Isso evita que
`SisTer-test` fique sem scripts, documentos ou migrations que so existam como
alteracoes locais.

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

O comando e compativel com o fluxo antigo, mas a entrada operacional preferida
e `scripts/test/run.sh`, que prepara e executa o teste.

## Desenvolvimento

No worktree principal:

```bash
./scripts/db/up.sh dev
./scripts/db/migrate.sh dev
./scripts/db/check.sh dev
./scripts/run_quality.sh
```

Para executar o fluxo completo, incluindo servidor e teste dos endpoints:

```bash
./scripts/run_all.sh dev 8000
```

O comando rejeita `dev` quando executado fora do worktree principal.

URL esperada:

```bash
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:55434/sister'
```

## Teste reproduzivel

No worktree principal de desenvolvimento, escolha explicitamente a origem:

```bash
./scripts/test/run.sh head
./scripts/test/run.sh release
```

`head` sincroniza `SisTer-test` com o commit atual e recusa alteracoes locais
nao commitadas. `release` busca as tags em `origin` e seleciona a maior tag
semantica no formato `v<versao>`.

O orquestrador entra no worktree de teste e chama internamente
`./scripts/run_all.sh test 8001`. Uma execucao manual desse comando continua
possivel, desde que feita dentro de um worktree secundario.

Se a release selecionada for anterior a criacao de `scripts/run_all.sh`, o
comando interrompe com uma mensagem explicita. Nesse caso e necessario publicar
uma release mais nova contendo o fluxo reproduzivel.

URL esperada:

```bash
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:55435/sister'
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

## Uso profissional

A pasta separada protege o estado local, mas nao substitui integracao continua.
O fluxo esperado e:

1. desenvolver e executar `./scripts/run_all.sh dev` no worktree principal;
2. revisar e commitar todas as mudancas relevantes;
3. executar `./scripts/test/run.sh head`, que valida exatamente o commit;
4. publicar a tag somente depois da aprovacao;
5. executar `./scripts/test/run.sh release` para confirmar o artefato publicado;
6. repetir os mesmos comandos em CI, com banco de teste efemero.

O identificador do commit exibido por `prepare_worktree.sh` e a evidencia exata
do codigo testado. Alteracoes nao commitadas nunca entram silenciosamente no
ambiente de teste.
