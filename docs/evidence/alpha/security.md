---
schema: sister.governance.approval/1.0.0
stage: alpha
area: security
status: approved
decision: approve
reviewed_commit: "4568745edb6909b3e523b6bd0e2fff1027dbe9de"
approved_by: "Equipe de Engenharia"
approved_at: "2026-07-31T12:56:14-03:00"
next_stage: beta
---

# Aprovação de Segurança — Gate Alpha

## 1. Finalidade

Registrar a revisão de segurança formal do estágio **Alpha** do SisTer.

Esta aprovação não declara o SisTer pronto para produção. Ela confirma apenas que os controles previstos para o Alpha foram implementados e que não há risco impeditivo conhecido para a promoção.

## 2. Escopo da revisão

A revisão abrange:

- persistência de sessões;
- armazenamento de `session_token_hash`;
- uso de SHA-256 para o hash do token de sessão;
- `storage/migrations/006_identity_sessions.sql`;
- `storage/migrations/007_capabilities.sql`;
- API autenticada `/api/me/capabilities`;
- capacidade `sister.maturity.read`;
- autenticação, autorização, logs e tratamento de erro relacionados;
- testes unitários e de qualidade associados.

Não estão sendo aprovados neste gate:

- segurança final do gateway;
- identidade interna assinada em produção;
- mTLS;
- rotação final de chaves;
- hardening completo de `systemd`;
- testes de carga, invasão e recuperação exigidos para Gama;
- uso produtivo com dados sensíveis reais.

## 3. Evidências examinadas

- Commit avaliado: `4568745edb6909b3e523b6bd0e2fff1027dbe9de`
- resultado de `scripts/ci/test-unit.sh`;
- resultado de `./scripts/run_quality.sh`;
- relatório e atestação do gate Alpha;
- migration `006_identity_sessions.sql`;
- migration `007_capabilities.sql`;
- implementação de `session_token_hash`;
- implementação de `/api/me/capabilities`;
- testes da capacidade `sister.maturity.read`;
- configuração de cookies, autenticação e autorização aplicável;
- registro de riscos e ADRs de segurança relacionados.

## 4. Critérios de revisão

### Sessões

- [x] O token bruto de sessão não é persistido.
- [x] O banco armazena somente o hash do token.
- [x] A comparação do token é segura.
- [x] Sessões possuem expiração explícita.
- [x] Logout ou revogação invalidam a sessão.
- [x] Sessões expiradas podem ser removidas de forma controlada.
- [x] O bootstrap não é reaberto indevidamente após falha.

### Migrações e banco

- [x] Tabelas, chaves, índices e restrições são coerentes.
- [x] O hash de sessão possui unicidade quando necessária.
- [x] Campos de expiração e revogação estão presentes ou formalmente planejados.
- [x] A migration não expõe segredo em texto claro.
- [x] Existe rollback ou estratégia forward-only documentada.

### Capacidades e autorização

- [x] `/api/me/capabilities` exige autenticação.
- [x] A API não concede capacidades por inferência insegura.
- [x] A capacidade `sister.maturity.read` é testada.
- [x] A ausência de capacidade resulta em negação no backend.
- [x] A interface não é tratada como controle suficiente.
- [x] O menor privilégio é preservado.

### Proteção de dados e logs

- [x] Senhas, cookies e tokens não aparecem em logs.
- [x] Erros não expõem stack traces, SQL ou caminhos sensíveis.
- [x] Dados pessoais retornados pela API são minimizados.
- [x] `.env.example` e equivalentes não contêm credenciais reais.
- [x] Nenhum segredo novo foi incluído no Git.

### Limitações conhecidas

- [x] O repasse provisório do cookie ao Clima continua registrado como dívida bloqueante de Beta.
- [x] A identidade por cabeçalhos não é tratada como solução final.
- [x] O token compartilhado interno não é considerado controle definitivo.
- [x] Os serviços permanecem restritos a loopback ou rede privada em desenvolvimento.

### Testes

- [x] Testes unitários passaram.
- [x] Testes de autenticação passaram.
- [x] Testes de autorização passaram.
- [x] `run_quality.sh` passou no commit avaliado.
- [x] Não existe outra falha obrigatória de segurança aberta no gate Alpha.

## 5. Resultado da revisão

### Decisão

`approve`

Valores permitidos:

- `approve`
- `approve_with_conditions`
- `reject`
- `pending`

### Fundamentação

Controles de sessão, identidade e banco de dados verificados. Riscos residuais estão mapeados para mitigação no estágio Beta.

### Condições ou ressalvas

- `Nenhuma`

### Riscos residuais aceitos

- repasse provisório do cookie ao Sister-Clima, limitado ao desenvolvimento;
- identidade interna definitiva ainda não implementada;
- gateway especializado ainda pendente;
- testes de carga, segurança ofensiva e recuperação reservados aos gates posteriores.

### Pendências transferidas para Beta

- eliminar o repasse do cookie aos subsistemas;
- adotar identidade interna assinada, com audiência e expiração;
- implementar gateway especializado;
- remover cabeçalhos de identidade forjáveis;
- aplicar capacidades de forma conformante em Nexo e Clima;
- testar coexistência e rollback.

## 6. Aprovação

Somente após a revisão, atualizar o front matter:

```yaml
status: approved
decision: approve
approved_by: "Equipe de Engenharia"
approved_at: "2026-07-31T12:56:14-03:00"
reviewed_commit: "4568745edb6909b3e523b6bd0e2fff1027dbe9de"
```

A aprovação significa:

> Os controles de identidade, sessão e capacidades avaliados atendem aos requisitos mínimos do Alpha. Não foi identificado risco crítico impeditivo, permanecendo registradas as limitações a tratar antes de Beta, Gama e Produção.

## 7. Assinatura da decisão

- Responsável: `Equipe de Engenharia`
- Data: `2026-07-31T12:56:14-03:00`
- Commit avaliado: `4568745edb6909b3e523b6bd0e2fff1027dbe9de`
- Resultado: `approve`
