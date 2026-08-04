CREATE TABLE IF NOT EXISTS sister_participation_assessments (
  assessment_id text PRIMARY KEY,
  participation_id text NOT NULL REFERENCES sister_participation_contracts(participation_id),
  contract_digest text NOT NULL,
  evaluated_commit text NOT NULL,
  result text NOT NULL CHECK (result IN ('PASS', 'WARN', 'SHADOW', 'BLOCK', 'INCONCLUSIVE')),
  gate_effect text NOT NULL CHECK (gate_effect = 'none'),
  assessment jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sister_participation_assessments_participation_idx
  ON sister_participation_assessments (participation_id, created_at);

INSERT INTO sister_schema_migrations (version)
VALUES ('009_participation_assessments')
ON CONFLICT (version) DO NOTHING;
