CREATE TABLE IF NOT EXISTS sister_sessions (
  session_id text PRIMARY KEY,
  user_id text NOT NULL REFERENCES sister_users(user_id) ON DELETE CASCADE,
  session_token_hash text NOT NULL UNIQUE,
  issued_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  user_agent_hash text,
  ip_hash text
);

CREATE INDEX IF NOT EXISTS sister_sessions_user_idx
  ON sister_sessions(user_id);

CREATE INDEX IF NOT EXISTS sister_sessions_active_idx
  ON sister_sessions(expires_at)
  WHERE revoked_at IS NULL;

INSERT INTO sister_schema_migrations (version)
VALUES ('006_identity_sessions')
ON CONFLICT (version) DO NOTHING;
