# Registro Evolutivo de Princípios REA/RIT

Este diretório preserva princípios arquiteturais e epistemológicos que emergem
da evolução do SisTer, da Reflexive Engineering Attitude (REA) e da Integridade
Temporal (RIT).

A finalidade não é reescrever retrospectivamente a história conceitual. Cada
princípio deve preservar sua genealogia.

## Fonte autoritativa

Cada arquivo em `principios/` é fonte autoritativa de uma versão histórica de
um princípio.

São artefatos derivados e nunca devem ser editados manualmente:

```text
generated/principios_index.tex
generated/registry.json
```

Ambos são produzidos pelo mesmo gerador a partir das mesmas fontes.

## Identidade e versionamento

IDs são estáveis (`REARIT-P001`, `REARIT-P002`, ...). Um ID identifica uma
linhagem conceitual e não é reutilizado para outra ideia.

As versões usam SemVer `MAJOR.MINOR.PATCH`:

- `MAJOR`: alteração incompatível do significado normativo;
- `MINOR`: extensão conceitual compatível;
- `PATCH`: esclarecimento editorial sem alteração normativa.

A identidade histórica é o par:

```text
(REARIT-ID, REARIT-VERSION)
```

representado externamente como:

```text
REARIT-P001@0.1.0
```

Múltiplas versões do mesmo ID podem coexistir no registro.

## Estados

- `PROPOSTO`
- `ACEITO`
- `REVISADO`
- `DEPRECIADO`
- `SUPERSEDIDO`

## Metadados obrigatórios

```text
% REARIT-ID: REARIT-P001
% REARIT-VERSION: 0.1.0
% REARIT-STATUS: PROPOSTO
% REARIT-TITLE: ...
% REARIT-DATE: YYYY-MM-DD
% REARIT-ORIGIN: ...
% REARIT-SUPERSEDES:
% REARIT-SUPERSEDED-BY:
```

Quando presentes, `SUPERSEDES` e `SUPERSEDED-BY` devem usar uma chave histórica
completa, por exemplo `REARIT-P001@0.1.0`.

## Interface de máquina

`generated/registry.json` usa o contrato público
`sister.rearit.registry/1.0.0`.

Cada item expõe identidade, versão, estado, título, origem, genealogia,
localização da fonte e `source_sha256`.

A interface v0.1.0 serve para descoberta, referência e proveniência. Ela não
declara automaticamente adoção ou conformidade de nenhum componente.

## Verificação

```bash
python3 scripts/rea_rit_registry.py build
python3 scripts/rea_rit_registry.py check
python3 scripts/rea_rit_registry.py list --json
python3 tests/rea_rit_registry_test.py
```

`build` deve ser byte-idempotente para todos os artefatos derivados.

## Regra de autoridade documental

Conhecimento derivável dos princípios não deve ser copiado manualmente para uma
segunda representação. Índices, catálogos e interfaces de máquina devem ser
gerados a partir das fontes autoritativas.
