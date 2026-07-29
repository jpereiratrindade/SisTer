CREATE TABLE IF NOT EXISTS sister_users (
  user_id text PRIMARY KEY,
  email text UNIQUE NOT NULL,
  full_name text NOT NULL,
  global_role text NOT NULL DEFAULT 'registered_user', -- guest, registered_user, researcher, project_lead, admin
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_project_groups (
  group_id text PRIMARY KEY,
  project_code text NOT NULL UNIQUE,
  name text NOT NULL,
  description text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_group_members (
  group_id text NOT NULL REFERENCES sister_project_groups(group_id),
  user_id text NOT NULL REFERENCES sister_users(user_id),
  role_in_group text NOT NULL DEFAULT 'researcher', -- coordinator, researcher, collaborator, observer
  joined_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (group_id, user_id)
);

ALTER TABLE sister_packages
  ADD COLUMN IF NOT EXISTS project_group_id text REFERENCES sister_project_groups(group_id),
  ADD COLUMN IF NOT EXISTS created_by_user_id text REFERENCES sister_users(user_id);

ALTER TABLE sister_evidence
  ADD COLUMN IF NOT EXISTS project_group_id text REFERENCES sister_project_groups(group_id),
  ADD COLUMN IF NOT EXISTS created_by_user_id text REFERENCES sister_users(user_id);

ALTER TABLE sister_knowledge_artifacts
  ADD COLUMN IF NOT EXISTS project_group_id text REFERENCES sister_project_groups(group_id),
  ADD COLUMN IF NOT EXISTS created_by_user_id text REFERENCES sister_users(user_id);

INSERT INTO sister_contracts (contract_id, contract_version, schema_uri, status)
VALUES
  ('user_identity', '1.0.0', 'contracts/user_identity.schema.json', 'active')
ON CONFLICT (contract_id) DO NOTHING;

INSERT INTO sister_schema_migrations (version)
VALUES ('003_user_profiles_and_groups')
ON CONFLICT (version) DO NOTHING;
