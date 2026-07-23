# Containers

## Recomendacao

Usar containers faz sentido para o SisTer, especialmente para o banco de dados.

Recomendacao inicial:

- containerizar PostgreSQL com pgvector desde ja;
- usar volume persistente para dados do banco;
- manter o C++ core e a interface em modo local durante a prototipagem;
- containerizar a aplicacao SisTer quando houver servidor/API ou processo de ingestao persistente.
- manter ambientes `dev` e `test` separados por container, porta e volume.
- usar `podman run` como fallback no Silverblue quando `podman-compose` ainda nao estiver instalado.

Essa separacao reduz atrito no desenvolvimento C++ e ja estabiliza a dependencia mais sensivel: o banco.

## Banco de dados

O banco deve rodar com dados persistentes. Em Docker Compose ou Podman Compose, isso significa montar um volume em:

```text
/var/lib/postgresql/data
```

Extensao esperada:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Variaveis esperadas pelo SisTer:

```bash
SISTER_DATABASE_URL=postgresql://sister:sister@localhost:55434/sister
SISTER_DATABASE_URL=postgresql://sister:sister@localhost:55435/sister
```

`55434` e reservado para desenvolvimento; `55435` e reservado para teste.

## Aplicacao

Enquanto o SisTer ainda esta em fase de core C++ + interface estatica, ha tres modos:

1. `local-dev`
   Compila C++ no host e serve `web/` com `python3 -m http.server`.

2. `db-container`
   Banco em container persistente, aplicacao local. Este e o modo recomendado agora.

3. `full-container`
   Banco, API/servidor e interface em containers. Deve vir depois que houver servidor SisTer.

## Persistencia

Nunca tratar o banco como efemero em ambiente de trabalho real.

Dados persistentes previstos:

- catalogo de sistemas;
- contratos firmados;
- pacotes importados;
- evidencias e proveniencia;
- objetos territoriais;
- embeddings;
- diagnosticos;
- auditoria.

## Proximo incremento tecnico

Artefatos iniciais criados:

```text
compose.yml
docker/db/Dockerfile
storage/migrations/001_init.sql
scripts/db/up.sh
scripts/db/down.sh
scripts/db/destroy.sh
scripts/db/check.sh
scripts/db/migrate.sh
scripts/dev/run_postgres.sh
scripts/test/create_worktree.sh
```

O `compose.yml` sobe uma imagem local baseada em `pgvector/pgvector:pg17`, usando volume nomeado por ambiente.

No Silverblue, se `podman-compose`, `docker-compose` e `docker compose` nao estiverem disponiveis, os scripts usam `podman build` e `podman run` diretamente.

Enquanto o servidor SisTer ainda nao possui acesso real ao banco, use:

```bash
./scripts/db/up.sh dev
cmake -S . -B build
cmake --build build
./scripts/db/check.sh dev
./scripts/db/migrate.sh dev
./build/apps/sisterd/sisterd 8000 web
```

Para teste isolado, crie um worktree e use o banco de teste:

```bash
./scripts/test/create_worktree.sh
cd ../SisTer-test
./scripts/db/up.sh test
./scripts/db/migrate.sh test
./scripts/run_quality.sh
```

Detalhes: [ENVIRONMENTS.md](./ENVIRONMENTS.md).
