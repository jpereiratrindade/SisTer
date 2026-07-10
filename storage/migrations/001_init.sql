CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sister_schema_migrations (
  version text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_systems (
  system_id text PRIMARY KEY,
  system_name text NOT NULL,
  system_version text NOT NULL,
  contract_version text NOT NULL,
  system_type text NOT NULL,
  public_scope text NOT NULL DEFAULT 'restricted',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_contracts (
  contract_id text PRIMARY KEY,
  contract_version text NOT NULL,
  schema_uri text NOT NULL,
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_packages (
  package_id text PRIMARY KEY,
  source_system_id text NOT NULL REFERENCES sister_systems(system_id),
  contract_version text NOT NULL,
  checksum text NOT NULL,
  validation_status text NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  public_scope text NOT NULL DEFAULT 'restricted'
);

CREATE TABLE IF NOT EXISTS sister_evidence (
  evidence_id text PRIMARY KEY,
  source_system_id text NOT NULL REFERENCES sister_systems(system_id),
  object_id text NOT NULL,
  kind text NOT NULL,
  uri text NOT NULL,
  checksum text,
  captured_at timestamptz NOT NULL,
  public_scope text NOT NULL DEFAULT 'private'
);

CREATE TABLE IF NOT EXISTS sister_territorial_objects (
  object_id text PRIMARY KEY,
  source_system_id text NOT NULL REFERENCES sister_systems(system_id),
  object_type text NOT NULL,
  spatial_context jsonb,
  confidence numeric,
  public_scope text NOT NULL DEFAULT 'restricted',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_knowledge_artifacts (
  artifact_id text PRIMARY KEY,
  source_ref text NOT NULL,
  artifact_type text NOT NULL,
  content text NOT NULL,
  embedding vector(768),
  public_scope text NOT NULL DEFAULT 'restricted',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_service_diagnostics (
  diagnostic_id text PRIMARY KEY,
  service_name text NOT NULL,
  status text NOT NULL,
  score numeric NOT NULL,
  summary text NOT NULL,
  public_scope text NOT NULL DEFAULT 'public',
  observed_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sister_knowledge_artifacts_embedding_idx
  ON sister_knowledge_artifacts
  USING ivfflat (embedding vector_cosine_ops);

INSERT INTO sister_contracts (contract_id, contract_version, schema_uri, status)
VALUES
  ('system_manifest', '0.1.0', 'contracts/system_manifest.schema.json', 'active'),
  ('camposync_package', '0.1.0', 'contracts/camposync_package.schema.json', 'active'),
  ('evidence', '0.1.0', 'contracts/evidence.schema.json', 'active'),
  ('public_scope', '0.1.0', 'contracts/public_scope.schema.json', 'active')
ON CONFLICT (contract_id) DO NOTHING;

INSERT INTO sister_schema_migrations (version)
VALUES ('001_init')
ON CONFLICT (version) DO NOTHING;
