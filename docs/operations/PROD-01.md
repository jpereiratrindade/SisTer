# PROD-01 — Production Readiness Assessment

`PROD-01` agrega evidências técnicas e operacionais antes de qualquer decisão
de promoção. Ele não autoriza produção. A decisão permanece explicitamente
`AWAITING_AUTHORIZATION`.

## Executar

Primeiro gere o relatório de qualidade no commit que será avaliado. Para exigir
os testes dinâmicos do gateway, configure o HAProxy nativo:

```bash
export GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22
./scripts/run_quality.sh
python3 scripts/prod01_readiness.py
```

O relatório sanitizado fica em `.run/production/prod01-readiness.json`.
O comando retorna `0` somente quando G1 a G5 estão `PASS`. Retorna `2` quando
há bloqueios ou evidências operacionais pendentes.

## Estados

```text
G1 Plataforma        PASS | BLOCKED
G2 Segurança         PASS | BLOCKED
G3 Operação          PASS | PENDING | BLOCKED
G4 Recuperação       PASS | PENDING | BLOCKED
G5 Observabilidade   PASS | PENDING | BLOCKED
G6 Promoção          AWAITING_AUTHORIZATION

Technical status     BLOCKED | NOT_READY | READY_FOR_PROMOTION
Decision             AWAITING_AUTHORIZATION
Production authorized false
```

`READY_FOR_PROMOTION` significa que os cinco gates técnicos agregados passaram.
Não significa que a implantação foi autorizada.

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

Mesmo após `READY_FOR_PROMOTION`, a revisão formal deve confirmar backup,
rollback, janela, exposição, capacidade, recuperação e aprovações. O preflight
continua obrigatório antes de cada ativação:

```bash
sudo ./scripts/sec03v_env_preflight.py \
  --haproxy-bin /usr/local/sbin/haproxy-3.2.22
```

Somente a governança pode mudar a decisão para autorizada. O script não possui
uma opção que converta evidência técnica em autorização operacional.
