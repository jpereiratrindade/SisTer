# PROD-01 — Playbook de Fechamento

Este playbook fecha o ciclo de promoção do SisTer Core sem criar gates novos.
O caminho continua sendo `PROD-01`: G1 a G5 produzem prontidão técnica, G6
produz decisão de governança.

## Pré-condições

- executar no host candidato;
- usar um commit limpo;
- manter `GATEWAY_HAPROXY_BIN` apontando para o HAProxy nativo validado;
- preservar os relatórios gerados em `.run/production/`;
- versionar somente evidências reais, com comandos, host, operador, data e
  resultados observados.

```bash
git status --short
git rev-parse HEAD
export GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22
./scripts/run_quality.sh
python3 scripts/prod01_readiness.py
```

Antes de G3-G5, o resultado esperado é `NOT_READY` ou `BLOCKED`, conforme o
estado local. Não force `PASS` em evidência que não foi executada.

## G3 Operação

Criar `docs/evidence/operations/PROD-01-G3-operations.md` somente após registrar:

- instalação ou conferência das unidades oficiais `sisterd.socket`,
  `sisterd.service` e `sister-gateway.service`;
- início, parada e reinício de `sisterd` pelos serviços oficiais;
- reinício do HAProxy;
- recuperação após reboot do host;
- execução controlada de migrations;
- atualização de configuração;
- recarga ou troca controlada de certificado;
- coleta de logs para diagnóstico;
- confirmação de ausência de dependência de usuário interativo.

Evidência parcial já registrada:

- `docs/evidence/operations/PROD-01-G3-gateway-test-isolation.md` — isolamento
  entre a suíte dinâmica do gateway e o socket operacional LAN.

O arquivo deve terminar com `status: PASS` somente quando todos os controles
acima tiverem evidência observável.

## G4 Recuperação

Criar `docs/evidence/operations/PROD-01-G4-recovery.md` somente após registrar:

- backup do PostgreSQL;
- restauração em ambiente isolado;
- validação de integridade após restauração;
- autenticação após restauração;
- implantação de versão ou configuração nova;
- falha simulada;
- rollback;
- serviço restaurado após rollback.

Este gate não aceita apenas existência de scripts. A evidência precisa mostrar
execução bem-sucedida de backup, restore e rollback.

## G5 Observabilidade

Criar `docs/evidence/operations/PROD-01-G5-observability.md` somente após
registrar:

- health check da aplicação;
- confirmação da conexão com o banco;
- estado dos serviços;
- logs do gateway;
- logs do `sisterd`;
- identificação de falhas de autenticação;
- identificação de erros internos;
- procedimento de diagnóstico;
- falha simulada detectável.

O objetivo mínimo da MVP é responder se o serviço está funcionando, qual
componente falhou e onde está a evidência.

## Prontidão Técnica

Depois de G3-G5:

```bash
./scripts/run_quality.sh
python3 scripts/prod01_readiness.py
```

Resultado esperado antes da autorização:

```text
G1 Plataforma         PASS
G2 Segurança          PASS
G3 Operação           PASS
G4 Recuperação        PASS
G5 Observabilidade    PASS
G6 Promoção           AWAITING_AUTHORIZATION

Technical status ........ READY
Decision ................ AWAITING_AUTHORIZATION
Production authorized ... false
MVP version ............. v0.1.0
Product maturity ........ Beta
Core state .............. Promotion pending
Operational state ....... Promotion pending
Recommended tag ......... prod-mvp-v0.1.0
```

Revisar antes de G6:

- `.run/production/prod01-readiness.json`;
- `.run/production/PROD-01-promotion-report.md`;
- evidências G1-G5;
- commit avaliado;
- plano de rollback;
- escopo da release;
- limitações conhecidas da MVP.

## G6 Autorização

Criar `docs/evidence/operations/PROD-01-G6-authorization.md` somente depois da
revisão operacional. Formato mínimo:

```yaml
Gate: PROD-01-G6
Decision: AUTHORIZED
commit: <sha completo avaliado>
release: v0.1.0
git_tag: prod-mvp-v0.1.0
scope: SisTer Core — Produção MVP
product_maturity: Beta
authorized_by: <responsável>
authorized_at: <data e hora ISO-8601>
rollback_reference: docs/evidence/operations/PROD-01-G4-recovery.md
known_limitations: <limitações aceitas>
evidence:
  - .run/production/prod01-readiness.json
  - .run/production/PROD-01-promotion-report.md
```

O commit no G6 precisa ser exatamente o mesmo commit avaliado pelo
`prod01_readiness.py`.

## Fechamento Final

```bash
python3 scripts/prod01_readiness.py
```

Resultado esperado:

```text
Technical status ........ READY
Decision ................ AUTHORIZED
Production authorized ... true
MVP version ............. v0.1.0
Product maturity ........ Beta
Core state .............. Produção MVP
Operational state ....... Produção MVP
Recommended tag ......... prod-mvp-v0.1.0
```

Formulação oficial:

```text
O núcleo SisTer está tecnicamente pronto e, mediante autorização G6 para o
commit validado, pode ser promovido como primeiro MVP em produção controlada,
versão v0.1.0, mantendo maturidade funcional Beta.
```

Somente depois disso:

```bash
git tag -a prod-mvp-v0.1.0 -m "SisTer Core v0.1.0 — Produção MVP"
git push origin main
git push origin prod-mvp-v0.1.0
```

Não reutilize nem mova a tag histórica `v0.1.0`, que pertence ao protótipo
inicial do repositório.

Depois da tag, o próximo trabalho deve iniciar a integração do primeiro
subsistema piloto sobre o contrato mínimo de subsistemas, não outro gate de
produção.
