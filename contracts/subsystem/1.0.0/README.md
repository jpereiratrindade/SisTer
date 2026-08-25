# sister.subsystem/1.0.0

Contrato comum de subsistema do SisTer.

> [!NOTE]
> **Enquadramento Constitutivo e de Compatibilidade (SIS-FDBK-01):**
> O contrato `sister.subsystem/1.0.0` especifica o **binding HTTP histórico de integração** entre o `sisterd` e processos de subsistemas. Ele é mantido para compatibilidade operacional e testes de baseline.
> Conforme o Documento Fundacional v0.2.0 e o ARC-01, a fronteira ontológica do participante SisTer é **semântica e independente de transporte**. Ter um servidor HTTP próprio é uma escolha de binding local de engenharia, não uma exigência ontológica para participar do SisTer.

Esta versão define a superfície mínima para que um subsistema seja integrado de
forma governada, testável e independente de regras específicas no núcleo.

## Artefatos

- `manifest.schema.json`: manifesto aprovado do subsistema;
- `capabilities.schema.json`: capacidades ofertadas pelo subsistema em execução;
- `identity-claims.schema.json`: claims mínimos da asserção interna Ed25519,
  restrita por audiência, capacidade, finalidade e correlação;
- `identity.schema.json`: identidade observada após mediação pelo SisTer;
- `echo.schema.json`: resposta do percurso funcional canônico;
- `health.schema.json`: saúde sanitizada do processo;
- `readiness.schema.json`: prontidão sanitizada para tráfego útil;
- `error.schema.json`: erro comum de integração;
- `audit-event.schema.json`: evento mínimo de auditoria;
- `openapi.yaml`: superfície técnica interna obrigatória;
- `interface.json`: descritor executável das rotas, autenticação e falhas;
- `examples/`: manifestos e respostas válidas para subsistemas existentes.

## Regras

- O contrato exato é `sister.subsystem/1.0.0`.
- Endpoints canônicos são `/manifest`, `/health`, `/ready`, `/capabilities`,
  `/identity` e `/echo`.
- Caminhos `/_sister/*` e `/api/*` são aliases transitórios e não comprovam
  conformidade.
- O endpoint interno deve ser local ou privado e nunca fornecido pelo usuário.
- Capacidades são declaradas, documentadas e negadas por padrão.
- Identidade interna é modelada aqui; assinatura operacional pertence ao WP-05.
- Dados públicos ou administrativos devem ser sanitizados antes de exposição.
- Acesso externo é mediado pelo gateway e pelo `sisterd`; subsistema não publica
  listener autônomo.
