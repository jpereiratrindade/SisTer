# Banco de Dados SisTer

## Objetivo

Definir a arquitetura planejada de persistencia do SisTer com PostgreSQL, PostGIS e pgvector.

O banco deve sustentar:

- catalogo de sistemas federados;
- contratos e versoes;
- pacotes CampoSync;
- evidencias e proveniencia;
- objetos territoriais;
- camadas e contexto espacial;
- artefatos de conhecimento;
- embeddings e analises vetoriais;
- diagnostico tecnico dos servicos;
- trilha de auditoria e governanca.

## Decisao tecnica

### PostgreSQL

Banco relacional principal para dados operacionais, historico, auditoria e consultas consistentes.

### PostGIS

Extensao geoespacial para:

- geometrias de areas, pontos, trajetos e camadas;
- consultas por intersecao, proximidade e cobertura;
- associacao entre observacoes, missoes, evidencias e territorios.

### pgvector

Extensao vetorial para:

- embeddings de textos, diagnosticos, evidencias textuais e artefatos de conhecimento;
- busca por similaridade semantica;
- identificacao de duplicidades ou proximidades conceituais;
- recuperacao de conhecimento produzido em integracoes anteriores.

## Extensoes

Configuracao esperada:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
```

## Variavel de ambiente

Nome planejado:

```bash
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:5432/sister'
```

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
  geom geometry,
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
CREATE INDEX sister_territorial_objects_geom_idx
  ON sister_territorial_objects
  USING gist (geom);

CREATE INDEX sister_knowledge_artifacts_embedding_idx
  ON sister_knowledge_artifacts
  USING ivfflat (embedding vector_cosine_ops);
```

## Porta de persistencia no C++

O dominio nao deve depender diretamente de PostgreSQL.

Direcao planejada:

- `core`: entidades, contratos, validacao e portas;
- `storage/postgres`: implementacao PostgreSQL/PostGIS/pgvector;
- `apps`: CLI, servidor ou ferramentas que conectam as portas a implementacoes.

## Proximos passos

1. Criar migracoes SQL versionadas.
2. Definir `SISTER_DATABASE_URL` e script local de desenvolvimento.
3. Criar porta C++ para persistencia de sistemas, contratos, evidencias e diagnosticos.
4. Adicionar implementacao PostgreSQL separada do dominio.
5. Alimentar a interface a partir de agregados publicos/restritos permitidos.
