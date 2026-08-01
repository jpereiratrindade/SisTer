---
schema: sister.governance.approval/1.0.0
stage: alpha
area: architecture
status: approved
decision: approve
reviewed_commit: "4568745edb6909b3e523b6bd0e2fff1027dbe9de"
approved_by: "Equipe de Engenharia"
approved_at: "2026-07-31T12:56:14-03:00"
next_stage: beta
---

# Aprovação de Arquitetura — Gate Alpha

## 1. Finalidade

Registrar a revisão arquitetural formal do estágio **Alpha** do SisTer.

Este documento não substitui os testes automatizados. Ele registra a deliberação humana sobre a coerência arquitetural das evidências produzidas para o commit avaliado.

## 2. Escopo da revisão

A revisão abrange:

- `storage/migrations/006_identity_sessions.sql`;
- `storage/migrations/007_capabilities.sql`;
- uso explícito de `session_token_hash` no `AuthStore`;
- API autenticada `/api/me/capabilities`;
- teste da capacidade `maturity.evidence.read`;
- `scripts/ci/test-unit.sh`;
- integração dessas evidências ao gate Alpha;
- impacto sobre `sisterd`, contratos, persistência e governança.

Não estão sendo aprovados neste gate:

- gateway especializado definitivo;
- remoção completa do proxy WebSocket artesanal;
- identidade interna assinada em produção;
- conformidade final de Clima e Nexo;
- prontidão Beta, Gama ou Produção.

## 3. Evidências examinadas

- Commit avaliado: `4568745edb6909b3e523b6bd0e2fff1027dbe9de`
- `.run/maturity/latest.json`
- `.run/maturity/history/index.json`
- relatório Markdown do gate Alpha, quando disponível;
- resultado de `scripts/ci/test-unit.sh`;
- resultado de `./scripts/run_quality.sh`;
- migrations `006_identity_sessions.sql` e `007_capabilities.sql`;
- implementação e testes de `/api/me/capabilities`;
- ADRs e documentos de arquitetura aplicáveis.

## 4. Critérios de revisão

### Separação de responsabilidades

- [x] A persistência de sessões não introduz acesso indevido entre domínios.
- [x] A API de capacidades permanece responsabilidade do núcleo de controle.
- [x] O `sisterd` não recebeu nova lógica específica de Clima ou Nexo.
- [x] O trabalho reduz, e não amplia, o acoplamento estrutural.

### Integração orientada por contratos

- [x] As capacidades são conceitos explícitos e versionáveis.
- [x] A implementação não depende exclusivamente de nomes de perfis.
- [x] A API pode evoluir para o contrato comum de autorização.
- [x] Não foi criado formato ad hoc incompatível com a arquitetura-alvo.

### Persistência e evolução

- [x] As migrations são coerentes com o histórico e a política do projeto.
- [x] A nova persistência não exige remoção imediata e irreversível do caminho legado.
- [x] Há estratégia de coexistência, migração ou rollback.
- [x] O estado após reinício permanece previsível.

### Coerência com o Alpha

- [x] As entregas correspondem às fundações previstas para Alpha.
- [x] Nenhuma entrega Beta foi declarada concluída antecipadamente.
- [x] As limitações provisórias permanecem registradas.
- [x] O gate continua cumulativo e baseado em evidências.

### Governança

- [x] O commit avaliado está identificado de forma inequívoca.
- [x] Testes e relatórios correspondem ao commit avaliado.
- [x] As decisões relevantes estão cobertas por ADRs.
- [x] Não há exceção arquitetural sem responsável, prazo e plano de remoção.

## 5. Resultado da revisão

### Decisão

`approve`

Valores permitidos:

- `approve`
- `approve_with_conditions`
- `reject`
- `pending`

### Fundamentação

As validações automatizadas confirmam a aderência aos contratos. A arquitetura está pronta para avançar ao estágio Beta.

### Condições ou ressalvas

- `Nenhuma`

### Riscos residuais aceitos

- `Nenhum`

### Pendências transferidas para Beta

- contrato comum `sister.subsystem/1.0.0`;
- gateway especializado;
- adaptadores conformantes de Nexo e Clima;
- identidade interna assinada;
- remoção do cookie na fronteira interna;
- registry orientado por manifestos.

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

> A implementação avaliada atende aos critérios arquiteturais definidos para o estágio Alpha, preserva a direção da arquitetura de produção e pode avançar à Beta mantendo as limitações registradas.

## 7. Assinatura da decisão

- Responsável: `Equipe de Engenharia`
- Data: `2026-07-31T12:56:14-03:00`
- Commit avaliado: `4568745edb6909b3e523b6bd0e2fff1027dbe9de`
- Resultado: `approve`
