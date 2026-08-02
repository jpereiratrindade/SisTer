# Evidências dos gates de maturidade

Os arquivos deste diretório registram aprovações e evidências humanas que não
podem ser inferidas somente pelo código. Uma aprovação deve conter, no mínimo:

```yaml
stage: gamma
area: security
status: approved
commit: <sha completo>
approved_by: <nome ou papel>
approved_at: <data ISO-8601>
evidence:
  - <relatório, teste ou decisão>
notes: <ressalvas>
```

O verificador não cria aprovações. Ele apenas comprova que o arquivo exigido
existe e contém `status: approved` ou `status: aprovado`.

## Segurança

- [SEC-01C/01D — robustez HTTP e contenção de abuso](./security/SEC-01C-01D.md)
- [SEC-02V — validação formal da identidade interna](./security/SEC-02V.md)
- [SEC-02M — promoção governada e política exata](./security/SEC-02M.md)
- [SEC-03B — gateway mínimo em laboratório](./security/SEC-03B.md)
- [SEC-03C — contenção de abuso e recursos](./security/SEC-03C.md)
- [ISO-01 — isolamento local do upstream](./security/ISO-01.md)
- [MAES-SisTer/1.0](../security/MAES_SISTER_1_0.md)

## Operação

- [DEV-ORCH-01 — classificação composta do ambiente local](./operations/DEV-ORCH-01.md)
- [DEV-ORCH-02 — propriedade e encerramento seguro do processo](./operations/DEV-ORCH-02.md)
