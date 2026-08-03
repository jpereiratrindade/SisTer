# Contratos de reflexividade operacional — 1.0.0

Materialização do `REF-00`, conforme [ADR-REF-01](../../../docs/adr/ADR-REF-01-reflexivity-profiles-and-authority.md).

Esta versão define a linguagem de máquina do piloto `RFP-NC-01`: perfil,
referências congeladas, evidências e avaliações. O piloto opera em
`D2–D3/A1/shadow`, sem efeito operacional e sem ações corretivas automáticas.

## Escopo

Inclui schemas, enums e exemplos para validação de contrato. Não inclui
`AssessmentEngine`, persistência definitiva, executor corretivo ou promoção de
autoridade.

## Invariantes

- `result`, `severity`, `gate_effect` e `proposed_action` são independentes;
- evidência insuficiente não pode produzir conclusão afirmativa;
- `shadow` declara efeito operacional nulo;
- toda referência e avaliador são identificáveis e versionados;
- uma avaliação não concede autoridade para corrigir.
