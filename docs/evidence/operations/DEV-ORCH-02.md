# DEV-ORCH-02 — propriedade e encerramento seguro do processo

**Data:** 2026-08-02

**Estado:** `PROVEN_IN_DEVELOPMENT`

## Controle

O PID file deixou de conter apenas um número. `serve.sh` grava atomicamente um
registro `0600` com:

```text
schema
pid
uid efetivo
ambiente
executável absoluto no worktree
instante de início do kernel (/proc/<pid>/stat)
```

Antes de sinalizar, `stop.sh` exige arquivo regular não symlink, owner e modo
seguros, e compara o registro com `/proc/<pid>/exe`, `/proc/<pid>/cmdline`,
`/proc/<pid>/environ`, UID e instante de início. Um PID reutilizado, arquivo
legado, ambiente divergente ou executável diferente bloqueia a parada.
O sinal é enviado por `pidfd`, depois de uma segunda validação ligada ao mesmo
objeto de processo, evitando a janela entre conferir um PID e sinalizá-lo.

`run_all.sh` e `serve.sh` não ignoram falha de `stop.sh`. Estados:

```text
sem PID file                       → continua
registro válido, processo ausente → remove registro stale e continua
identidade válida                 → SIGTERM, espera e confirma saída
identidade inválida               → recusa sinal, exit 3
processo não encerrou             → exit 1
```

## Evidência reproduzida

```text
registro adulterado/reutilizado   → recusado; processo permaneceu vivo
executável diferente              → recusado; processo permaneceu vivo
processo ausente                  → classificado stale sem sinal
sisterd real                      → registro 0600 validado e parada confirmada
run_all com PID file estrangeiro  → exit 3; processo estrangeiro permaneceu vivo
testes unitários                  → 7/7 PASS
```

O controle governa somente processos locais iniciados pelos scripts de
desenvolvimento. Ele não substitui a propriedade de processos do systemd nem
autoriza o gate SEC-03V.
