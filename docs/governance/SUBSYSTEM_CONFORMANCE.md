# Conformidade de subsistemas SisTer

## Regra

`sister.subsystem/1.0.0` é a fronteira normativa. A implementação canônica é
`reference/sister-reference`; ela prova a plataforma, mas não é elegível para
produção nem certifica produtos externos.

## Estados

```text
QUARANTINED
  -> CONTRACT_VALID
  -> LIFECYCLE_VALID
  -> IDENTITY_VALID
  -> TRANSPORT_VALID
  -> FAILURE_VALID
  -> ELIGIBLE_FOR_INTEGRATION
  -> AUTHORIZED
```

Transições são monotônicas dentro de uma avaliação. Falha ou mudança do commit
avaliado invalida evidências posteriores e retorna o candidato a `QUARANTINED`.
Somente decisão humana registrada pode produzir `AUTHORIZED`.

## Evidências obrigatórias

| Estado | Evidência mínima |
| --- | --- |
| `CONTRACT_VALID` | manifesto válido e seis rotas canônicas |
| `LIFECYCLE_VALID` | início, readiness, parada e ownership governados |
| `IDENTITY_VALID` | identidade externa descartada e reconstruída pelo SisTer |
| `TRANSPORT_VALID` | loopback ou socket Unix; nenhuma porta pública autônoma |
| `FAILURE_VALID` | timeout, indisponibilidade, resposta inválida e erros sanitizados |
| `ELIGIBLE_FOR_INTEGRATION` | todas as evidências vinculadas ao mesmo commit |
| `AUTHORIZED` | decisão registrada com responsável, escopo e commit |

## API canônica

O descritor em `contracts/subsystem/1.0.0/interface.json` é a fonte executável:

```text
GET  /manifest
GET  /health
GET  /ready
GET  /capabilities
GET  /identity
POST /echo
```

`identity` e `echo` exigem mediação interna autenticada. Acesso externo usa
exclusivamente `/integrations/<id>/*` pelo gateway SisTer. Aliases existentes
são compatibilidade transitória e não contam como evidência de conformidade.

## Promoção

Conformidade não publica nem autoriza automaticamente. A saída da quarentena
exige ADR ou adendo, atualização explícita do registro, testes no perfil
governado e autorização para o mesmo commit.
