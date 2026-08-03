# Contrato de execução — 1.0.0

Primeira materialização de `EXEC-01`: uma execução integrada deve ser
identificável, idempotente, persistível e reconstruível antes de ser consumida
por proveniência ou reflexividade.

O contrato separa `execution_status` de `validity_status`. Retry e
reprocessamento sempre criam uma nova execução relacionada à anterior.
