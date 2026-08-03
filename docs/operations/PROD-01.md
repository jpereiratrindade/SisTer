# PROD-01 — Production Readiness Assessment

`PROD-01` agrega evidências técnicas e operacionais e orquestra o ciclo de
promoção do núcleo SisTer. Ele não cria autorização por inferência: a promoção
produtiva só muda para `AUTHORIZED` quando existe uma evidência G6 explícita
para o mesmo commit avaliado.

## Executar

Primeiro gere o relatório de qualidade no commit que será avaliado. Para exigir
os testes dinâmicos do gateway, configure o HAProxy nativo:

```bash
export GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22
./scripts/run_quality.sh
python3 scripts/prod01_readiness.py
```

O relatório sanitizado fica em `.run/production/prod01-readiness.json`. O
workflow também escreve `.run/production/PROD-01-promotion-report.md` e
`.run/production/core-state.json` com a consolidação da promoção. O comando
retorna `0` somente quando G1 a G5 estão `PASS`. Retorna `2` quando há
bloqueios ou evidências operacionais pendentes. O roteiro operacional completo
está em [`PROD-01-CLOSURE.md`](PROD-01-CLOSURE.md).

## Estados

```text
G1 Plataforma        PASS | BLOCKED
G2 Segurança         PASS | BLOCKED
G3 Operação          PASS | PENDING | BLOCKED
G4 Recuperação       PASS | PENDING | BLOCKED
G5 Observabilidade   PASS | PENDING | BLOCKED
G6 Promoção          AWAITING_AUTHORIZATION | AUTHORIZED | BLOCKED

Technical status     BLOCKED | NOT_READY | READY
Decision             AWAITING_AUTHORIZATION | AUTHORIZED | BLOCKED
Production authorized false | true
```

`READY` significa que os cinco gates técnicos agregados passaram. Não significa
que a implantação foi autorizada. `Production authorized true` só aparece quando
G6 está `AUTHORIZED` para o mesmo commit.

## Classificação

`PROD-01` separa três dimensões que não devem ser misturadas:

| Conceito | Estado no primeiro MVP | Significado |
| --- | --- | --- |
| Estado do produto | `Beta` | maturidade funcional ainda sujeita a mudanças e aprendizado |
| Estado operacional | `Produção MVP` | ambiente controlado, autorizado e observável |
| Versão do marco | `v0.1.0` | primeira versão promovida do núcleo SisTer |
| Tag Git | `prod-mvp-v0.1.0` | tag publicável sem reusar a tag histórica `v0.1.0` |

A formulação oficial da promoção é:

```text
O núcleo SisTer está tecnicamente pronto e, mediante autorização G6 para o
commit validado, pode ser promovido como primeiro MVP em produção controlada,
versão v0.1.0, mantendo maturidade funcional Beta.
```

A tag Git `v0.1.0` já pertence ao protótipo inicial e não deve ser movida.
O GitHub Release do primeiro MVP de produção deve usar `prod-mvp-v0.1.0`.

## Evidências operacionais

Os gates G3, G4 e G5 exigem relatórios versionados, com `status: PASS`, no
commit avaliado:

- `docs/evidence/operations/PROD-01-G3-operations.md` — reinício, reboot,
  atualização, certificado e rotação de logs;
- `docs/evidence/operations/PROD-01-G4-recovery.md` — backup/restauração,
  rollback e reinício de `sisterd`/HAProxy;
- `docs/evidence/operations/PROD-01-G5-observability.md` — health, readiness,
  métricas, logs estruturados, auditoria e carga.

Cada relatório deve registrar commit, host, data, comandos, resultado, operador,
artefatos preservados e ressalvas. Um arquivo ausente é `PENDING`; um arquivo
presente sem `status: PASS` é `BLOCKED`.

## Promoção

Mesmo após `READY`, a revisão formal deve confirmar backup,
rollback, janela, exposição, capacidade, recuperação e aprovações. O preflight
continua obrigatório antes de cada ativação:

```bash
sudo ./scripts/sec03v_env_preflight.py \
  --haproxy-bin /usr/local/sbin/haproxy-3.2.22
```

Somente a governança pode mudar a decisão para autorizada. O script não possui
uma opção que converta evidência técnica em autorização operacional. Para
autorizar a promoção, registre uma evidência versionada em:

```text
docs/evidence/operations/PROD-01-G6-authorization.md
```

Formato mínimo:

```yaml
Gate: PROD-01-G6
Decision: AUTHORIZED
commit: <sha completo avaliado>
release: v0.1.0
git_tag: prod-mvp-v0.1.0
scope: SisTer Core — Produção MVP
product_maturity: Beta
authorized_by: <nome ou papel>
authorized_at: <data ISO-8601>
rollback_reference: docs/evidence/operations/PROD-01-G4-recovery.md
known_limitations: <limitações aceitas>
evidence:
  - .run/production/prod01-readiness.json
  - .run/production/PROD-01-promotion-report.md
```

Com G1 a G5 `PASS` e G6 `AUTHORIZED`, o workflow emite:

```text
Technical status ........ READY
Decision ................ AUTHORIZED
Production authorized ... true
MVP version ............. v0.1.0
Product maturity ........ Beta
Operational state ....... Produção MVP
```

Nesse ponto, `.run/production/PROD-01-promotion-report.md` consolida as
evidências e recomenda a criação da tag `prod-mvp-v0.1.0`;
`.run/production/core-state.json` registra o estado do núcleo como `Produção
MVP`, mantendo maturidade funcional `Beta`.
