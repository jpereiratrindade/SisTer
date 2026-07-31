# Aprovação de gate

```yaml
stage: gamma
area: security
status: pending
commit: <sha completo>
approved_by: <nome ou papel>
approved_at: <data ISO-8601>
evidence:
  - <arquivo ou relatório>
notes: <ressalvas e riscos aceitos>
```

Troque `pending` por `approved` somente após revisar as evidências do commit
indicado. A aprovação não deve ser reaproveitada automaticamente em outro
commit.
