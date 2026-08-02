# SEC-03V-ENV — ambiente candidato privilegiado

**Data:** 2026-08-02  
**Host:** Fedora 44 Workstation  
**Estado:** `READY`  
**Próximo gate autorizado:** execução de `SEC-03V` sem skips  
**Merge, MAES aprovado e tag `v0.2.8`:** não autorizados

## Baseline avaliada

```text
SisTer   f4b8435d8dde1f005a83dce396abb7be021686cb
Nexo     f77196ed8dbd30fc009066a73086972dcd4c437c
HAProxy  sister-haproxy-lab-3.2.22-1.sistersec03v.fc44.x86_64
```

O HAProxy pertence ao RPM assinado pela chave de laboratório com fingerprint
`ED3F4CE4C756983F211097B6AB5D893C71F31D65`, instalado pela transação DNF
`135` e sem divergência em `rpm -V`. A proveniência completa permanece em
[HAPROXY-RPM-01.json](./HAPROXY-RPM-01.json).

## Relatório executável

```text
schema   sister.sec03v-env-preflight/1.0.0
result   READY
checks   42
PASS     42
BLOCKED  0
SHA-256  b4e3a2782b18ef96e2a9a9acc167439f1b31c74f08c6ff7042b13aa6e7c569f0
```

O original sanitizado está preservado no host em
`/var/lib/sister-sec03v-env/sec03v-env-preflight.json`, `root:root 0600`. Uma
cópia de trabalho com o mesmo digest foi revisada sem encontrar valores de
configuração ou segredos.

## Controles comprovados

| Fronteira | Resultado |
| --- | --- |
| revisões e instalação | worktrees limpos; revisão SisTer instalada corresponde ao commit avaliado |
| identidades | `sister` e `sister-gateway` não interativos; grupo `haproxy` restrito |
| configuração e chaves | owner, grupo, modos, par Ed25519 e acesso sob a identidade real aprovados |
| upstream local | `/run/sister` governado; socket `sister:haproxy 0660`; nenhuma porta `8000` |
| gateway | RPM assinado, configuração offline válida e processo systemd sob `sister-gateway` |
| exposição candidata | listener único `127.0.0.1:8443`, TLS 1.3 e Host candidato exato |
| prontidão SisTer | health TLS alcançou `sisterd` com PostgreSQL `connected` |
| prontidão Nexo | health e PostgreSQL `READY`; modo assinado com `kid=identity-2026-08` validado separadamente |

## Achados fechados durante a aplicação

1. `/etc/sister root:root 0750` impedia as contas de serviço de alcançar seus
   arquivos governados. ACLs nomeadas de travessia, sem leitura ou escrita,
   foram documentadas e o preflight passou a executar o teste sob as
   identidades reais (`b19b8f7`).
2. `/run/sister root:haproxy 0750` impedia o `sisterd` de executar `lstat()` no
   pathname do descritor ativado. O contrato `tmpfiles` passou a aplicar
   `u:sister:--x`, sem incluir `sister` no grupo do gateway (`83f0642`). A
   tentativa anterior falhou fechada, manteve a porta `8000` ausente e expôs
   somente `503` controlado no loopback.
3. O volume PostgreSQL persistente possuía senha divergente da configuração
   local. A credencial do papel `sister` foi sincronizada sem registro do valor
   e validada por autenticação TCP. O preflight passou a rejeitar health `200`
   quando `database` não for `connected` (`f4b8435`).

As três correções foram exercitadas no host, passaram em `26/26` testes do
núcleo e foram publicadas na branch `sec-03v-env`. Os sete testes dinâmicos do
gateway continuaram `SKIP` nessa execução de qualidade porque pertencem ao gate
seguinte; eles não foram usados para declarar `SEC-03V` aprovado.

## Riscos residuais e limites

- O certificado é exclusivo do laboratório candidato, com validade curta, e
  não autoriza exposição produtiva.
- O listener do gateway permanece somente em loopback; nenhuma porta HTTP
  pública foi aberta.
- `root`, comprometimento das contas autorizadas e comprometimento integral do
  host permanecem fora da proteção oferecida por owner, modo e ACL.
- O relatório comprova prontidão do ambiente, não a matriz dinâmica completa de
  framing, headers, abuso, clientes lentos, falhas e resiliência.

## Decisão

`SEC-03V-ENV-B` está concluído e `SEC-03V-ENV` está `READY`. A única promoção
autorizada por esta evidência é iniciar `SEC-03V` no ambiente preservado, sem
skips. Merge coordenado, atualização do MAES como aprovado e criação da
`v0.2.8` continuam condicionados ao resultado desse gate.
