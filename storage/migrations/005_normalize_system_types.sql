-- Migration 005: corrige system_type do sister_campo para consistência com os demais sistemas
-- O valor 'field_integration_system' (em inglês, da migration 002) é normalizado para
-- 'Integracao de campo', alinhando com os demais tipos definidos em português.

UPDATE sister_systems
SET system_type = 'Integracao de campo'
WHERE system_id = 'sister_campo'
  AND system_type = 'field_integration_system';

INSERT INTO sister_schema_migrations (version)
VALUES ('005_normalize_system_types')
ON CONFLICT (version) DO NOTHING;
