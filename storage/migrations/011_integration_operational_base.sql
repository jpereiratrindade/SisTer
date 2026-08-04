CREATE TABLE IF NOT EXISTS sister_capability_offers (
  offer_id text PRIMARY KEY,
  subsystem_id text NOT NULL,
  capability text NOT NULL,
  contract_digest text NOT NULL CHECK (contract_digest ~ '^sha256:[a-f0-9]{64}$'),
  contract jsonb NOT NULL,
  signature jsonb,
  signature_verified boolean NOT NULL DEFAULT false,
  status text NOT NULL CHECK (status IN ('proposed', 'active', 'deprecated', 'suspended')),
  published_at timestamptz NOT NULL,
  registered_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_capability_requirements (
  requirement_id text PRIMARY KEY,
  subsystem_id text NOT NULL,
  needed_capability text NOT NULL,
  contract_digest text NOT NULL CHECK (contract_digest ~ '^sha256:[a-f0-9]{64}$'),
  contract jsonb NOT NULL,
  signature jsonb,
  signature_verified boolean NOT NULL DEFAULT false,
  status text NOT NULL CHECK (status IN ('proposed', 'active', 'satisfied', 'suspended')),
  published_at timestamptz NOT NULL,
  registered_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_integration_definitions (
  integration_id text NOT NULL,
  version text NOT NULL,
  offer_id text NOT NULL REFERENCES sister_capability_offers(offer_id),
  requirement_id text NOT NULL REFERENCES sister_capability_requirements(requirement_id),
  objective text NOT NULL,
  contract_digest text NOT NULL CHECK (contract_digest ~ '^sha256:[a-f0-9]{64}$'),
  contract jsonb NOT NULL,
  signature jsonb,
  signature_verified boolean NOT NULL DEFAULT false,
  approval_status text NOT NULL CHECK (approval_status IN ('draft', 'approved', 'rejected', 'superseded')),
  approval_authority text NOT NULL,
  approved_by text,
  approved_at timestamptz,
  registered_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (integration_id, version),
  CHECK (approval_status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL AND signature_verified))
);

CREATE TABLE IF NOT EXISTS sister_integration_executions (
  execution_id text PRIMARY KEY,
  integration_id text NOT NULL,
  integration_version text NOT NULL,
  status text NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
  contract_digest text NOT NULL CHECK (contract_digest ~ '^sha256:[a-f0-9]{64}$'),
  execution jsonb NOT NULL,
  started_at timestamptz NOT NULL,
  finished_at timestamptz,
  registered_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (integration_id, integration_version)
    REFERENCES sister_integration_definitions(integration_id, version)
);

CREATE TABLE IF NOT EXISTS sister_integration_assessments (
  assessment_id text PRIMARY KEY,
  integration_id text NOT NULL,
  integration_version text NOT NULL,
  execution_id text NOT NULL REFERENCES sister_integration_executions(execution_id),
  result text NOT NULL CHECK (result IN ('confirmed', 'divergent', 'inconclusive')),
  recommendation_action text NOT NULL,
  human_decision_required boolean NOT NULL DEFAULT false,
  assessment jsonb NOT NULL,
  assessed_at timestamptz NOT NULL,
  registered_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (integration_id, integration_version)
    REFERENCES sister_integration_definitions(integration_id, version)
);

CREATE INDEX IF NOT EXISTS sister_integration_definitions_approval_idx
  ON sister_integration_definitions (approval_status, signature_verified, registered_at DESC);

CREATE INDEX IF NOT EXISTS sister_integration_assessments_integration_idx
  ON sister_integration_assessments (integration_id, integration_version, assessed_at DESC);

INSERT INTO sister_schema_migrations (version)
VALUES ('011_integration_operational_base')
ON CONFLICT (version) DO NOTHING;
