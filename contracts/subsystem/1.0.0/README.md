# sister.subsystem/1.0.0

Contrato comum de subsistema do SisTer.

Esta versão define a superfície mínima para que um subsistema seja integrado de
forma governada, testável e independente de regras específicas no núcleo.

## Artefatos

- `manifest.schema.json`: manifesto aprovado do subsistema;
- `capabilities.schema.json`: capacidades ofertadas pelo subsistema em execução;
- `identity-claims.schema.json`: claims mínimos da asserção interna Ed25519,
  restrita por audiência, capacidade, finalidade e correlação;
- `health.schema.json`: saúde sanitizada do processo;
- `readiness.schema.json`: prontidão sanitizada para tráfego útil;
- `error.schema.json`: erro comum de integração;
- `audit-event.schema.json`: evento mínimo de auditoria;
- `openapi.yaml`: superfície técnica interna obrigatória;
- `examples/`: manifestos e respostas válidas para subsistemas existentes.

## Regras

- O contrato exato é `sister.subsystem/1.0.0`.
- Endpoints técnicos ficam sob `/_sister/`.
- O endpoint interno deve ser local ou privado e nunca fornecido pelo usuário.
- Capacidades são declaradas, documentadas e negadas por padrão.
- Identidade interna é modelada aqui; assinatura operacional pertence ao WP-05.
- Dados públicos ou administrativos devem ser sanitizados antes de exposição.
