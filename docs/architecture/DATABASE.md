# Banco de Dados SisTer

## Objetivo

Definir a arquitetura planejada de persistencia do SisTer com PostgreSQL e pgvector.

O banco deve sustentar:

- catalogo de sistemas federados;
- contratos e versoes;
- pacotes CampoSync;
- evidencias e proveniencia;
- objetos territoriais;
- contexto espacial representado inicialmente sem extensao geoespacial;
- artefatos de conhecimento;
- embeddings e analises vetoriais;
- diagnostico tecnico dos servicos;
- trilha de auditoria e governanca.

## Decisao tecnica

### PostgreSQL

Banco relacional principal para dados operacionais, historico, auditoria e consultas consistentes.

### pgvector

Extensao vetorial para:

- embeddings de textos, diagnosticos, evidencias textuais e artefatos de conhecimento;
- busca por similaridade semantica;
- identificacao de duplicidades ou proximidades conceituais;
- recuperacao de conhecimento produzido em integracoes anteriores.

## Extensoes

Configuracao esperada:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Variavel de ambiente

Nomes planejados:

```bash
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:55434/sister'
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:55435/sister'
```

`55434` e usado pelo ambiente `dev`; `55435` e usado pelo ambiente `test`.

Se `SISTER_DATABASE_URL` nao estiver definido, ferramentas locais podem operar em modo arquivo/demonstracao quando isso for suficiente.

## Esboco de tabelas

Este esboco ainda nao e migracao canonica.

```sql
CREATE TABLE sister_systems (
  system_id text PRIMARY KEY,
  system_name text NOT NULL,
  system_version text NOT NULL,
  contract_version text NOT NULL,
  system_type text NOT NULL,
  public_scope text NOT NULL DEFAULT 'restricted',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sister_contracts (
  contract_id text PRIMARY KEY,
  contract_version text NOT NULL,
  schema_uri text NOT NULL,
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sister_packages (
  package_id text PRIMARY KEY,
  source_system_id text NOT NULL REFERENCES sister_systems(system_id),
  contract_version text NOT NULL,
  checksum text NOT NULL,
  validation_status text NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  public_scope text NOT NULL DEFAULT 'restricted'
);

CREATE TABLE sister_evidence (
  evidence_id text PRIMARY KEY,
  source_system_id text NOT NULL REFERENCES sister_systems(system_id),
  object_id text NOT NULL,
  kind text NOT NULL,
  uri text NOT NULL,
  checksum text,
  captured_at timestamptz NOT NULL,
  public_scope text NOT NULL DEFAULT 'private'
);

CREATE TABLE sister_territorial_objects (
  object_id text PRIMARY KEY,
  source_system_id text NOT NULL REFERENCES sister_systems(system_id),
  object_type text NOT NULL,
  spatial_context jsonb,
  confidence numeric,
  public_scope text NOT NULL DEFAULT 'restricted',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sister_knowledge_artifacts (
  artifact_id text PRIMARY KEY,
  source_ref text NOT NULL,
  artifact_type text NOT NULL,
  content text NOT NULL,
  embedding vector(768),
  public_scope text NOT NULL DEFAULT 'restricted',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sister_service_diagnostics (
  diagnostic_id text PRIMARY KEY,
  service_name text NOT NULL,
  status text NOT NULL,
  score numeric NOT NULL,
  summary text NOT NULL,
  public_scope text NOT NULL DEFAULT 'public',
  observed_at timestamptz NOT NULL DEFAULT now()
);
```

## Politica de exposicao por coluna

Toda tabela operacional relevante deve possuir `public_scope` com valores planejados:

- `public`: pode ser publicado em dashboards e relatorios abertos;
- `restricted`: pode circular internamente ou para parceiros autorizados;
- `private`: exige controle de acesso, justificativa de finalidade e minimizacao.

## Indices planejados

```sql
CREATE INDEX sister_knowledge_artifacts_embedding_idx
  ON sister_knowledge_artifacts
  USING ivfflat (embedding vector_cosine_ops);
```

## Porta de persistencia no C++

O dominio nao deve depender diretamente de PostgreSQL.

Direcao planejada:

- `core`: entidades, contratos, validacao e portas;
- `storage/postgres`: implementacao PostgreSQL/pgvector;
- `apps`: CLI, servidor ou ferramentas que conectam as portas a implementacoes.

## Artefatos iniciais

Foram criados:

- `compose.yml`;
- `docker/db/Dockerfile`;
- `storage/migrations/001_init.sql`;
- `scripts/db/up.sh`;
- `scripts/db/down.sh`;
- `scripts/db/destroy.sh`;
- `scripts/db/check.sh`;
- `scripts/db/migrate.sh`;
- `scripts/test/create_worktree.sh`;
- `scripts/dev/run_postgres.sh`.
- `scripts/dev/db_check.sh`;
- `scripts/dev/db_migrate.sh`.

Comandos de desenvolvimento:

```bash
./scripts/db/up.sh dev
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:55434/sister'
./scripts/db/check.sh dev
./scripts/db/migrate.sh dev
```

Comandos de teste:

```bash
./scripts/test/create_worktree.sh
cd ../SisTer-test
./scripts/db/up.sh test
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:55435/sister'
./scripts/db/check.sh test
./scripts/db/migrate.sh test
```

Os comandos de banco usam `psql` local quando disponivel. Se `psql` nao estiver instalado, usam `docker exec` no container do ambiente selecionado.

## Proximos passos

1. Criar porta C++ para persistencia de sistemas, contratos, evidencias e diagnosticos.
2. Adicionar implementacao PostgreSQL separada do dominio.
3. Alimentar a interface a partir de agregados publicos/restritos permitidos.

Ver tambem:

- [CONTAINERS.md](./CONTAINERS.md)
- [ENVIRONMENTS.md](./ENVIRONMENTS.md)
