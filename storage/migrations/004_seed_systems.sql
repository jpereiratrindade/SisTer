-- Migration 004: Seed dos sistemas integrados canônicos
-- Move os dados que estavam hardcoded em main.cpp para o banco como fonte de verdade.

INSERT INTO sister_systems (system_id, system_name, system_version, contract_version, system_type, public_scope)
VALUES
  ('sister_campo',  'SisTer-Campo',   '1.0.0', 'camposync.package/1.0.0',       'Integracao de campo',    'restricted'),
  ('sister_nexo',   'SisTer Nexo',    '1.0.0', 'sister-nexo.integration/1.0.0', 'Governanca cientifica',  'restricted'),
  ('sister_clima',  'Sister-Clima',   '1.0.0', 'sister-contracts/0.1.0',         'Climatico',              'restricted'),
  ('sister_studio', 'Sister-Studio',  '1.0.0', 'sister-studio.integration/1.0.0','Criativo',               'restricted')
ON CONFLICT (system_id) DO NOTHING;

INSERT INTO sister_contracts (contract_id, contract_version, schema_uri, status)
VALUES
  ('sister_clima_governance',   '1.0.0', 'contracts/sister_clima_governance.schema.json',   'active'),
  ('sister_studio_integration', '1.0.0', 'contracts/sister_studio_integration.schema.json', 'active'),
  ('sister_nexo_integration',   '1.0.0', 'contracts/sister_nexo_integration.schema.json',   'active')
ON CONFLICT (contract_id) DO NOTHING;

INSERT INTO sister_schema_migrations (version)
VALUES ('004_seed_systems')
ON CONFLICT (version) DO NOTHING;
