CREATE TABLE IF NOT EXISTS sister_capabilities (
  capability_id text PRIMARY KEY,
  description text NOT NULL,
  risk_level text NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sister_role_capabilities (
  role_name text NOT NULL,
  capability_id text NOT NULL REFERENCES sister_capabilities(capability_id) ON DELETE CASCADE,
  granted_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (role_name, capability_id)
);

INSERT INTO sister_capabilities (capability_id, description, risk_level)
VALUES
  ('sister.maturity.read', 'Ler evidências administrativas de maturidade.', 'low'),
  ('subsystem.manifest.read', 'Ler manifestos aprovados de subsistemas.', 'low'),
  ('nexo.projects.read', 'Ler projetos científicos autorizados.', 'low'),
  ('climate.dashboard.read', 'Ler painéis climáticos integrados.', 'low')
ON CONFLICT (capability_id) DO NOTHING;

INSERT INTO sister_role_capabilities (role_name, capability_id)
VALUES
  ('admin', 'sister.maturity.read'),
  ('admin', 'subsystem.manifest.read'),
  ('admin', 'nexo.projects.read'),
  ('admin', 'climate.dashboard.read')
ON CONFLICT (role_name, capability_id) DO NOTHING;

INSERT INTO sister_schema_migrations (version)
VALUES ('007_capabilities')
ON CONFLICT (version) DO NOTHING;
