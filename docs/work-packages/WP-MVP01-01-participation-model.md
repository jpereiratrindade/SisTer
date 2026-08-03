# WP-MVP01-01 - Modelo mínimo de participação

## Objetivo

Materializar a proposta de participação da referência sem conceder autorização,
persistência ou efeito operacional.

## Estado

`TESTADO_EM_MEMORIA`.

## Entregas

- `ParticipationContract` encapsulado e criado por fábrica validada;
- identificadores fortes de participação, capacidade e contribuição;
- `CapabilityDefinition`, `ContributionDefinition` e `AuthorityAllocation`;
- `BoundaryObjectEnvelope` com contexto, autoridade, integridade e proveniência;
- `ParticipationAssessment` separado da decisão de autorização;
- estado inicial obrigatório `proposed`;
- perfil reflexivo inicial obrigatório `D2/A1/shadow`;
- schemas 1.0.0 e exemplo canônico da referência;
- exemplos negativos para impedir autoautorização pelo contrato ou assessment;
- validação de schema inteiramente local, sem resolução de rede.

## Invariantes

- referência não decide sua própria autorização;
- oferta exige ao menos uma capacidade e uma contribuição;
- capacidade duplicada é rejeitada;
- toda dimensão de autoridade deve possuir responsável explícito;
- este WP não altera `sister.subsystem/1.0.0`.

## Fora do escopo

Motor de assessment, decisão humana, transições após `proposed`, persistência,
HTTP, CLI e execução de capacidade.

## Gate

```bash
ctest --test-dir build -R 'sister_core_tests|participation_contract_tests'
```
