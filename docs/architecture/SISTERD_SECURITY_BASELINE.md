# Baseline de segurança do `sisterd`

**Release de referência:** `v0.2.5`  
**Estado:** baseline executável de pré-produção  
**Atualização:** 1 de agosto de 2026

## Finalidade

Este documento consolida o estado implementado após a quarentena de transporte,
a autorização por capacidades e o endurecimento do bootstrap administrativo. Ele
não promove o SisTer a produção: registra quais invariantes já são executáveis e
quais entregas ainda bloqueiam essa promoção.

## Controles concluídos

| Controle | Estado | Garantia implementada |
|---|---|---|
| SEC-00 — quarentena do transporte | Concluído | produção aceita somente loopback e recusa os proxies HTTP/WebSocket legados |
| SEC-01 — autorização por capacidades | Concluído | rotas sensíveis declaram capacidade e falham fechadas |
| SEC-01A — remoção do RBAC residual | Concluído | papel alimenta o catálogo inicial, mas não autoriza diretamente rotas sensíveis |
| SEC-01B — bootstrap administrativo offline | Concluído | produção proíbe bootstrap HTTP; o comando local cria um único administrador sem sessão |

As decisões normativas estão nas ADRs
[0015](../adr/ADR-0015-sisterd-transport-quarantine.md),
[0016](../adr/ADR-0016-capability-based-authorization.md) e
[0017](../adr/ADR-0017-offline-administrator-bootstrap.md).

## Configuração mínima de produção

```text
SISTER_ENV=production
SISTER_BIND_HOST=127.0.0.1
SISTER_ENABLE_HTTP_BOOTSTRAP=false
SISTER_ENABLE_LEGACY_PROXY=false
SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY=false
SISTER_AUTH_FILE=/var/lib/sister/auth-users.tsv
```

Uma combinação incompatível falha antes de expor o serviço. O listener continua
sendo interno: TLS, WebSocket, limites e observabilidade de transporte pertencem
ao gateway especializado.

## Bootstrap operacional

Antes do primeiro login, executar localmente sob o usuário do serviço:

```bash
sudo -u sister env SISTER_AUTH_FILE=/var/lib/sister/auth-users.tsv \
  /opt/sister/build/apps/sisterctl/sisterctl \
  auth bootstrap-admin "Administrador SisTer" admin@example.org
```

O comando exige caminho explícito e absoluto, lê a senha sem eco, grava o arquivo
com permissão `0600`, não cria `.sessions` e recusa uma segunda tentativa. O
comando `auth-import-user` não é uma alternativa normal ao bootstrap: ele é um
procedimento local de migração/manutenção *break-glass*, com serviço parado,
backup e rollback.

## Fronteiras e limitações

- O log estruturado de autorização é evidência operacional; ainda não é uma
  trilha de auditoria governada com retenção e integridade próprias.
- Recurso e finalidade são registrados, mas a decisão desta baseline avalia a
  capacidade declarada.
- O proxy legado e o repasse de cookie podem continuar no laboratório somente
  quando habilitados de forma explícita; são proibidos em produção.
- O armazenamento em arquivo ainda não serializa duas execuções locais do
  bootstrap iniciadas exatamente ao mesmo tempo. A operação deve ser única até
  existir bloqueio interprocesso ou criação exclusiva.
- A unidade `systemd` aplica hardening inicial, mas não substitui o gate completo
  de segurança, carga, recuperação e operação.

## Próximas entregas bloqueantes

1. **SEC-02 — identidade interna assinada:** asserção curta, audiência restrita,
   rotação e rejeição de identidade forjável.
2. Gateway especializado e adaptadores conformantes para Nexo e Clima.
3. Eliminação definitiva do cookie na fronteira interna e remoção física dos
   proxies legados.
4. Persistência transacional e governança completas de auditoria, políticas e
   sessões.
5. Testes de carga, segurança ofensiva, recuperação e prontidão operacional.

## Evidência reproduzível

Antes de publicar a release:

```bash
./scripts/run_quality.sh
./scripts/app/smoke.sh <porta-do-sisterd>
git diff --check
```

O gate exige que testes unitários, integração do `sisterctl`, contratos,
governança, maturidade e validações de `systemd` sejam aprovados. As tags já
publicadas são imutáveis; correções posteriores recebem uma nova versão SemVer.
