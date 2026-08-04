# ADR-0025: Limite de persistência da participação no MVP-01

## Estado

Aceito para a consolidação do `PDE-MVP01-01`.

## Decisão

No MVP-01, o `sisterd` é a autoridade funcional para registrar e consultar
candidaturas de participação. O PostgreSQL é a fonte de verdade durável. O
`sisterctl` é uma interface operacional e não mantém um repositório paralelo
como fonte de verdade.

O contrato persistido permanece em `proposed`. Persistência não autoriza a
participação, capacidade ou execução. A autorização continua dependente de
avaliação e decisão humana separadas.

## Consequência

O armazenamento local criado durante o protótipo é evidência experimental. A
operação pública `participation propose` deverá passar pelo `sisterd` e pela
tabela `sister_participation_contracts`, criada na migração `008`.

## Invariantes

- `sisterctl` não grava diretamente no PostgreSQL;
- o identificador da participação é único;
- somente contratos válidos e em `proposed` podem ser registrados;
- nova avaliação ou decisão não altera retroativamente o contrato persistido;
- toda mudança posterior preserva digest, commit de origem e proveniência.
