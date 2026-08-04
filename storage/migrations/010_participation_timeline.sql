CREATE TABLE IF NOT EXISTS sister_participation_events (
  event_id text PRIMARY KEY,
  event_type text NOT NULL CHECK (event_type IN ('ParticipationProposed', 'TechnicalAssessmentCompleted')),
  process_id text NOT NULL CHECK (process_id = 'P-MVP01-PARTICIPATION'),
  aggregate_id text NOT NULL REFERENCES sister_participation_contracts(participation_id),
  actor text NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  causation_id text,
  correlation_id text NOT NULL,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  payload jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS sister_participation_events_timeline_idx
  ON sister_participation_events (aggregate_id, occurred_at);

INSERT INTO sister_schema_migrations (version)
VALUES ('010_participation_timeline')
ON CONFLICT (version) DO NOTHING;
