# WP-REF-00 — Contratos centrais da reflexividade

## Objetivo

Materializar a linguagem de máquina definida pela ADR-REF-01 para o piloto Nexo–Compras.

## Estado

Concluído — Alfa / contrato arquitetural, com gate de validação aprovado.

## Referências

- [ADR-REF-01](../adr/ADR-REF-01-reflexivity-profiles-and-authority.md)
- [EFE-SisTer/1.4](../architecture/EFE_SISTER_1_4_REFLEXIVIDADE_CPP.tex)

## Entregas

- schemas versionados em `contracts/reflexivity/1.0.0`;
- perfil `RFP-NC-01` em `D2–D3/A1/shadow`;
- exemplos de contrato e avaliação;
- validação automatizada de exemplos válidos e inválidos;
- integração inicial ao SGE em modo `shadow`.

Evidência reproduzível:

```text
./scripts/contracts/validate-reflexivity.sh
```

Resultado: schemas, referências e exemplos positivos aceitos; combinações
`shadow` com gate não-shadow, ação corretiva ou efeito operacional rejeitadas.

## Fora de escopo

`AssessmentEngine` operacional, persistência definitiva, ações corretivas, promoção para A2/A3/A4 e C++26.

## Critério de aceite

Os schemas devem validar os exemplos, rejeitar autoridade ou efeito incompatível com o perfil inicial e preservar a separação entre resultado, severidade, gate, ação proposta e efeito operacional.
