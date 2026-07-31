# ADR-0013: Validação da Federação do Motor Declarativo

## Status

Aceita

## Contexto

O Motor Declarativo (SGE-SisTer) foi inicialmente concebido como um mecanismo para verificar a maturidade técnica do SisTer-Core (C++). Com a evolução arquitetural para uma plataforma federada (ADR-0001), surgiu a necessidade de governar múltiplos subsistemas independentes (como SisTer Nexo e Sister-Clima) sem acoplar a lógica de verificação ao núcleo do SisTer.

O piloto do Sister-Clima (Python/Streamlit) serviu como o teste de fogo para a generalização do motor. O motor precisava ser capaz de:
- Isolar a avaliação técnica da autoridade de governança (Modo Shadow).
- Executar verificações em stacks completamente diferentes (ex: Python/Pytest) usando scripts e perfis de maturidade próprios, sem "hardcodes" no avaliador.
- Preservar o histórico, as dimensões de saúde da engenharia e a rastreabilidade (commits, artefatos) de forma independente para o ecossistema federado.

## Decisão

Validamos que o Motor Declarativo atinge com sucesso o nível de maturidade necessário para operar como uma **infraestrutura de engenharia para um ecossistema de subsistemas**. 

Essa decisão consolida a separação entre:
1. **O Motor (SGE):** Infraestrutura genérica que lê yaml, executa scripts delegados e gera a árvore de decisão e rastreabilidade (evidências).
2. **O Perfil do Componente (yaml):** Onde reside o conhecimento de domínio específico, contratos, declarações de entrypoint e definições de dependências do subsistema, independentemente da stack tecnológica.

## Invariantes

- **Isolamento de Estado:** A falha técnica de um componente avaliado no modo `shadow` nunca afeta o estado global ou a promoção do SisTer-Core.
- **Autoridade Distribuída:** As verificações (`checks`) e as rotinas de segurança não pertencem ao `evaluator.py`, elas devem sempre ser referenciadas nos arquivos `yaml` dos perfis.
- **Nomenclatura do Centro de Engenharia:** Para preservar a neutralidade e evitar interpretações equivocadas institucionais, "Resultados" isolados referem-se estritamente à "Avaliação técnica" individual do componente.

## Consequências

- O Motor Declarativo deixa definitivamente de ser o "verificador do SisTer-Core" e assume o papel formal de árbitro federativo do ecossistema.
- O SisTer passa a conseguir absorver novos componentes (como Campo e Studio) através da simples criação de perfis `.yaml` e scripts de execução delegados.
- É estabelecida a fundação para uma possível evolução do SGE como um *framework* próprio de governança de engenharia.
