# Containers

## Recomendacao

Usar containers faz sentido para o SisTer, especialmente para o banco de dados.

Recomendacao inicial:

- containerizar PostgreSQL com PostGIS e pgvector desde ja;
- usar volume persistente para dados do banco;
- manter o C++ core e a interface em modo local durante a prototipagem;
- containerizar a aplicacao SisTer quando houver servidor/API ou processo de ingestao persistente.

Essa separacao reduz atrito no desenvolvimento C++ e ja estabiliza a dependencia mais sensivel: o banco.

## Banco de dados

O banco deve rodar com dados persistentes. Em Docker Compose ou Podman Compose, isso significa montar um volume em:

```text
/var/lib/postgresql/data
```

Extensoes esperadas:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
```

Variavel esperada pelo SisTer:

```bash
SISTER_DATABASE_URL=postgresql://sister:sister@localhost:5432/sister
```

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
scripts/dev/run_postgres.sh
```

O `compose.yml` sobe uma imagem local baseada em `postgis/postgis:16-3.4` com o pacote `postgresql-16-pgvector`, usando volume nomeado.

Enquanto o servidor SisTer ainda nao possui acesso real ao banco, use:

```bash
./scripts/dev/run_postgres.sh
cmake -S . -B build
cmake --build build
./build/apps/sisterctl/sisterctl db-check
./build/apps/sisterctl/sisterctl db-migrate
./build/apps/sisterd/sisterd 8000 web
```
