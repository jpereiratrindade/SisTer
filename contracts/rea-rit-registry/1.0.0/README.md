# sister.rearit.registry/1.0.0

Contrato público para a representação de máquina do **Registro Evolutivo de
Princípios REA/RIT**.

## Fonte de autoridade

O contrato não cria uma segunda fonte normativa. A fonte de verdade permanece:

```text
docs/rea-rit/principios/*.tex
```

`docs/rea-rit/generated/registry.json` é uma projeção determinística dessas
fontes e deve ser regenerada, nunca editada manualmente.

## Identidade histórica

`REARIT-ID` identifica a linhagem conceitual estável de um princípio.

Uma versão histórica é identificada pelo par:

```text
(REARIT-ID, REARIT-VERSION)
```

e exposta como chave:

```text
REARIT-P001@0.1.0
```

Isso permite preservar simultaneamente múltiplas versões do mesmo princípio.

## Genealogia

`supersedes` e `superseded_by`, quando presentes, referenciam uma **chave
histórica completa**, não apenas um ID.

## Proveniência

Cada item contém `source` e `source_sha256`. O hash SHA-256 ancora a projeção de
máquina aos bytes da fonte LaTeX autoritativa.

## Determinismo

O artefato não contém timestamp de build, `generated_at` nem outro dado
dependente do relógio. Para fontes idênticas, builds sucessivos devem produzir
bytes idênticos.

## Escopo desta versão

Esta versão oferece descoberta, identidade, versionamento, status, genealogia,
proveniência e referência estável por outros sistemas.

Ela **não** define ainda adoção de princípios por componentes, claims de
conformidade, assessments, decisões de governança nem integração específica com
Praxis, Infra ou qualquer outro consumidor.
