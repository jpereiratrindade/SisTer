CREATE TABLE IF NOT EXISTS sister_integration_decisions (
  decision_id text PRIMARY KEY,
  integration_id text NOT NULL,
  integration_version text NOT NULL,
  decision text NOT NULL CHECK (decision IN ('approved', 'rejected')),
  decided_by text NOT NULL,
  authority text NOT NULL,
  rationale text NOT NULL,
  decision_record jsonb NOT NULL,
  decided_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (integration_id, integration_version)
    REFERENCES sister_integration_definitions(integration_id, version)
);

CREATE INDEX IF NOT EXISTS sister_integration_decisions_integration_idx
  ON sister_integration_decisions (integration_id, integration_version, decided_at DESC);

INSERT INTO sister_schema_migrations (version)
VALUES ('013_integration_decisions')
ON CONFLICT (version) DO NOTHING;
