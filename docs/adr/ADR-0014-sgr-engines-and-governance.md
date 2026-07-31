# ADR-0014: Engines de verificação e modos de governança do SGR

## Status

Aceita

## Contexto

O SGR passou a operar em um ecossistema federado, com SisTer-Core e componentes
independentes avaliados por perfis declarativos. A evolução do verificador exige
separar duas decisões que antes podiam parecer uma só:

- qual engine executa os critérios de maturidade;
- qual autoridade o resultado técnico possui sobre gates e promoções.

Sem essa separação, falhas técnicas de componentes em piloto poderiam bloquear
promoções globais indevidamente, e diferenças entre o verificador legado e o
declarativo poderiam ser confundidas com falhas reais do produto.

## Decisão

Adotamos a distinção formal entre engines de verificação e modos de governança:

1. `compare` é o engine padrão durante a migração.
2. `declarative` é o motor de destino.
3. `legacy` é temporário e diagnóstico.
4. `shadow` avalia, registra e comunica sem bloquear promoções fora do escopo.
5. `governed` pode bloquear apenas no escopo declarado.
6. Maturidade técnica não implica automaticamente autoridade de bloqueio.

A referência canônica da política é
[Engines de verificação e modos de governança](../architecture/sgr/verification-engines-and-governance-modes.md).

## Invariantes

- O engine define como a maturidade é verificada.
- O modo de governança define que autoridade o resultado possui.
- Componentes em `shadow` podem falhar sem bloquear a promoção global.
- Componentes em `governed` só podem bloquear o escopo explicitamente declarado.
- Divergências em `compare` exigem investigação e registro.
- A retirada de `legacy` exige evidência de equivalência, cobertura declarativa e decisão formal.
- Alterar `governance_mode` é mudança arquitetural, não edição operacional trivial.

## Consequências

- O SGR ganha uma política explícita para migração do verificador.
- O ecossistema federado pode evoluir com pilotos avaliados sem impor bloqueios globais prematuros.
- O Painel de Maturidade deve apresentar resultado técnico e modo de governança como conceitos separados.
- Procedimentos operacionais de divergência passam a ser obrigatórios antes de aceitar mudanças de semântica.
- Promoções de `shadow` para `governed` exigem maturidade técnica, criticidade arquitetural e responsável operacional.
