# ADR-0026: Arquitetura de identidade, autenticação e sessões humanas

## Estado

Aceito como direção arquitetural; implementação incremental.

## Decisão

O SisTer será um relying party de OpenID Connect para autenticação humana em
implantações institucionais. O provedor de identidade será responsável por
senha, MFA, passkeys, recuperação e prova da identidade.

O `sisterd` continuará responsável por vincular a identidade externa a um
usuário SisTer, manter sessões opacas e aplicar autorização interna por
capacidades. Sessões, vínculos, capacidades e auditoria deverão ser
persistidos no PostgreSQL quando o modo institucional for implementado.

O `AuthStore` baseado em arquivo permanece permitido para desenvolvimento,
bootstrap offline e emergência controlada. Ele não é a arquitetura definitiva
de identidade nem fonte de verdade dos contratos de participação.

## Fronteiras

```text
IdP/OIDC       → prova a identidade humana
sisterd        → vínculo, sessão e autorização
PostgreSQL     → sessões, capacidades e auditoria duráveis
sisterctl      → cliente, sem armazenar senha
subsistemas    → identidade de serviço, nunca login humano
```

O código de domínio recebe apenas um principal autenticado, sem depender do
mecanismo que o produziu. A autorização não é inferida automaticamente de
claims do provedor: capacidades SisTer são resolvidas e auditadas localmente.

## Consequências

- o fluxo atual com `AuthStore` pode continuar sem bloquear o MVP-01;
- a migração futura para OIDC ocorre em um adaptador de identidade;
- `participation.propose` continua exigindo capacidade SisTer explícita;
- `sisterctl` não deve pedir ou armazenar senhas;
- sessões de navegador devem usar identificador opaco e cookie seguro;
- autenticação de subsistemas permanece separada da autenticação humana.
