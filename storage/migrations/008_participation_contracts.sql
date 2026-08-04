CREATE TABLE IF NOT EXISTS sister_participation_contracts (
  participation_id text PRIMARY KEY,
  participant_system_id text NOT NULL REFERENCES sister_systems(system_id),
  contract_version text NOT NULL,
  contract_digest text NOT NULL,
  state text NOT NULL CHECK (state = 'proposed'),
  contract jsonb NOT NULL,
  proposed_by text NOT NULL,
  authentication_source text NOT NULL DEFAULT 'AuthStore',
  source_commit text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sister_participation_contracts_system_idx
  ON sister_participation_contracts (participant_system_id, created_at);

INSERT INTO sister_contracts (contract_id, contract_version, schema_uri, status)
VALUES ('participation_contract', '1.0.0', 'contracts/participation/1.0.0/participation-contract.schema.json', 'active')
ON CONFLICT (contract_id) DO NOTHING;

INSERT INTO sister_schema_migrations (version)
VALUES ('008_participation_contracts')
ON CONFLICT (version) DO NOTHING;
