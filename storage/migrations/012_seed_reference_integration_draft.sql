DELETE FROM sister_integration_assessments
WHERE assessment_id = 'oa-int-sister_reference-0001';

DELETE FROM sister_integration_executions
WHERE execution_id = 'exec-int-sister_reference-0001';

DELETE FROM sister_integration_definitions
WHERE integration_id = 'int-sister_reference-reference-observation';

DELETE FROM sister_capability_requirements
WHERE requirement_id = 'req-sister-reference-observation';

DELETE FROM sister_capability_offers
WHERE offer_id = 'offer-sister_reference-reference-execution';

INSERT INTO sister_capability_offers
  (offer_id, subsystem_id, capability, contract_digest, contract, signature, signature_verified, status, published_at)
VALUES (
  'offer-sister_reference-echo-execute',
  'sister_reference',
  'reference.echo.execute',
  'sha256:06774dbeca3cf0d6e0ad7668f027c6666159ba7444cd5ca13a73836777de6d7a',
  $json${
    "offer_id": "offer-sister_reference-echo-execute",
    "subsystem_id": "sister_reference",
    "capability": "reference.echo.execute",
    "produces": ["sister.subsystem.echo/1.0.0"],
    "contract": {
      "schema_id": "sister.subsystem.echo",
      "version": "1.0.0",
      "uri": "contracts/subsystem/1.0.0/echo.schema.json"
    },
    "status": "active",
    "published_at": "2026-08-04T10:00:00Z"
  }$json$::jsonb,
  NULL,
  false,
  'active',
  '2026-08-04T10:00:00Z'
)
ON CONFLICT (offer_id) DO UPDATE SET
  capability = EXCLUDED.capability,
  contract_digest = EXCLUDED.contract_digest,
  contract = EXCLUDED.contract,
  signature_verified = false,
  status = EXCLUDED.status;

INSERT INTO sister_capability_requirements
  (requirement_id, subsystem_id, needed_capability, contract_digest, contract, signature, signature_verified, status, published_at)
VALUES (
  'req-sister-mediated-echo-observation',
  'sister',
  'observacao_de_execucao_mediada',
  'sha256:c108e2c8818e8c220a4c110f2f3840516b2ea911cc67b67b6d70bfde5d3235d7',
  $json${
    "requirement_id": "req-sister-mediated-echo-observation",
    "subsystem_id": "sister",
    "needed_capability": "observacao_de_execucao_mediada",
    "expected_contract": {
      "schema_id": "sister.subsystem.echo",
      "version": "1.0.0",
      "uri": "contracts/subsystem/1.0.0/echo.schema.json"
    },
    "purpose": "Verificar se o SisTer consegue mediar uma execução echo no sister_reference e observar o resultado sem acessar implementação interna.",
    "accepts_from": ["sister_reference"],
    "status": "active",
    "published_at": "2026-08-04T10:05:00Z"
  }$json$::jsonb,
  NULL,
  false,
  'active',
  '2026-08-04T10:05:00Z'
)
ON CONFLICT (requirement_id) DO UPDATE SET
  needed_capability = EXCLUDED.needed_capability,
  contract_digest = EXCLUDED.contract_digest,
  contract = EXCLUDED.contract,
  signature_verified = false,
  status = EXCLUDED.status;

INSERT INTO sister_integration_definitions
  (integration_id, version, offer_id, requirement_id, objective, contract_digest, contract, signature, signature_verified, approval_status, approval_authority)
VALUES (
  'int-sister_reference-mediated-echo',
  '1.0.0',
  'offer-sister_reference-echo-execute',
  'req-sister-mediated-echo-observation',
  'Executar a capacidade reference.echo.execute do sister_reference por mediação do SisTer e comparar a resposta observada com o valor esperado.',
  'sha256:7cd896e6fec85b837e8e70f27c733ccfac4da02724ced3e04347a2464162e0bd',
  $json${
    "integration_id": "int-sister_reference-mediated-echo",
    "version": "1.0.0",
    "objective": "Executar a capacidade reference.echo.execute do sister_reference por mediação do SisTer e comparar a resposta observada com o valor esperado.",
    "offer_id": "offer-sister_reference-echo-execute",
    "requirement_id": "req-sister-mediated-echo-observation",
    "source_subsystem_id": "sister_reference",
    "target_subsystem_id": "sister",
    "field_mappings": [
      {"from": "value", "to": "expected_value"},
      {"from": "value", "to": "observed_value"},
      {"from": "processed_by", "to": "executor"}
    ],
    "transformations": [
      "enviar payload echo pelo SisTer",
      "preservar value na resposta",
      "registrar processed_by como executor observado"
    ],
    "success_criteria": [
      "requisição mediada pelo SisTer",
      "resposta segue sister.subsystem.echo/1.0.0",
      "observed_value igual a expected_value",
      "executor observado igual a sister_reference"
    ],
    "required_evidence": [
      "contrato de oferta assinado",
      "contrato de requisito assinado",
      "definição de integração assinada",
      "execução com entrada e saída referenciadas por digest"
    ],
    "approval": {
      "status": "draft",
      "responsible": "engenharia.sister",
      "authority": "integration.approve"
    }
  }$json$::jsonb,
  NULL,
  false,
  'draft',
  'integration.approve'
)
ON CONFLICT (integration_id, version) DO UPDATE SET
  offer_id = EXCLUDED.offer_id,
  requirement_id = EXCLUDED.requirement_id,
  objective = EXCLUDED.objective,
  contract_digest = EXCLUDED.contract_digest,
  contract = EXCLUDED.contract,
  signature_verified = false,
  approval_status = 'draft',
  approved_by = NULL,
  approved_at = NULL;

INSERT INTO sister_integration_executions
  (execution_id, integration_id, integration_version, status, contract_digest, execution, started_at, finished_at)
VALUES (
  'exec-int-sister_reference-echo-0001',
  'int-sister_reference-mediated-echo',
  '1.0.0',
  'completed',
  'sha256:d1d55540255b79564bf2fe83bfa520b5f64f334750ed304caf7e4a434629c7db',
  $json${
    "execution_id": "exec-int-sister_reference-echo-0001",
    "integration_id": "int-sister_reference-mediated-echo",
    "integration_version": "1.0.0",
    "status": "completed",
    "observations": [
      "value preservado na resposta",
      "processed_by=sister_reference observado"
    ]
  }$json$::jsonb,
  '2026-08-04T10:30:00Z',
  '2026-08-04T10:30:02Z'
)
ON CONFLICT (execution_id) DO UPDATE SET
  integration_id = EXCLUDED.integration_id,
  integration_version = EXCLUDED.integration_version,
  status = EXCLUDED.status,
  contract_digest = EXCLUDED.contract_digest,
  execution = EXCLUDED.execution,
  finished_at = EXCLUDED.finished_at;

INSERT INTO sister_integration_assessments
  (assessment_id, integration_id, integration_version, execution_id, result, recommendation_action, human_decision_required, assessment, assessed_at)
VALUES (
  'oa-int-sister_reference-echo-0001',
  'int-sister_reference-mediated-echo',
  '1.0.0',
  'exec-int-sister_reference-echo-0001',
  'inconclusive',
  'request_human_decision',
  true,
  $json${
    "assessment_id": "oa-int-sister_reference-echo-0001",
    "integration_id": "int-sister_reference-mediated-echo",
    "execution_id": "exec-int-sister_reference-echo-0001",
    "expected": [
      "requisição mediada pelo SisTer",
      "resposta segue sister.subsystem.echo/1.0.0",
      "observed_value igual a expected_value",
      "executor observado igual a sister_reference"
    ],
    "observed": [
      "contrato declara capacidade real reference.echo.execute",
      "endpoint POST /echo existe no sister_reference",
      "assinatura formal ainda ausente"
    ],
    "result": "inconclusive",
    "recommendation": {
      "action": "request_human_decision",
      "summary": "Assinar a definição de integração echo mediada antes de promover esta capacidade como aprovada."
    },
    "human_decision_required": true,
    "assessed_at": "2026-08-04T10:31:00Z"
  }$json$::jsonb,
  '2026-08-04T10:31:00Z'
)
ON CONFLICT (assessment_id) DO UPDATE SET
  integration_id = EXCLUDED.integration_id,
  integration_version = EXCLUDED.integration_version,
  execution_id = EXCLUDED.execution_id,
  result = EXCLUDED.result,
  recommendation_action = EXCLUDED.recommendation_action,
  human_decision_required = EXCLUDED.human_decision_required,
  assessment = EXCLUDED.assessment,
  assessed_at = EXCLUDED.assessed_at;

INSERT INTO sister_schema_migrations (version)
VALUES ('012_seed_reference_integration_draft')
ON CONFLICT (version) DO NOTHING;
