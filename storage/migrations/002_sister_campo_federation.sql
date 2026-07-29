INSERT INTO sister_contracts (
  contract_id, contract_version, schema_uri, status
) VALUES (
  'camposync_package',
  '1.0.0',
  'contracts/camposync_package.schema.json',
  'active'
)
ON CONFLICT (contract_id) DO UPDATE SET
  contract_version = EXCLUDED.contract_version,
  schema_uri = EXCLUDED.schema_uri,
  status = EXCLUDED.status;

INSERT INTO sister_systems (
  system_id, system_name, system_version, contract_version,
  system_type, public_scope
) VALUES (
  'sister_campo',
  'SisTer-Campo',
  '0.4.0-dev',
  'camposync.package/1.0.0',
  'field_integration_system',
  'restricted'
)
ON CONFLICT (system_id) DO UPDATE SET
  system_name = EXCLUDED.system_name,
  system_version = EXCLUDED.system_version,
  contract_version = EXCLUDED.contract_version,
  system_type = EXCLUDED.system_type,
  public_scope = EXCLUDED.public_scope;

INSERT INTO sister_schema_migrations (version)
VALUES ('002_sister_campo_federation')
ON CONFLICT (version) DO NOTHING;
