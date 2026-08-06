ALTER TABLE sister_users
  ADD COLUMN IF NOT EXISTS password_salt text,
  ADD COLUMN IF NOT EXISTS password_hash text,
  ADD COLUMN IF NOT EXISTS password_iterations integer NOT NULL DEFAULT 210000,
  ADD COLUMN IF NOT EXISTS active boolean NOT NULL DEFAULT true,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE sister_users
  DROP CONSTRAINT IF EXISTS sister_users_global_role_check;

ALTER TABLE sister_users
  ADD CONSTRAINT sister_users_global_role_check
  CHECK (global_role IN ('guest', 'registered_user', 'researcher', 'project_lead', 'admin', 'user'));

INSERT INTO sister_schema_migrations (version)
VALUES ('011_local_auth_credentials')
ON CONFLICT (version) DO NOTHING;
