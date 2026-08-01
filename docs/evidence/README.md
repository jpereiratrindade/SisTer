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
- [SEC-02V — checklist de validação da identidade interna](./security/SEC-02V-CHECKLIST.md)
- [MAES-SisTer/1.0](../security/MAES_SISTER_1_0.md)
