# ADR-0007 — Nexo, operações de pesquisa e fronteira de compras

- Estado: aceito e implementado
- Data: 2026-07-29

## Contexto

Projetos de pesquisa precisam relacionar planejamento, ações, atividades,
responsáveis, evidências, publicações e recursos necessários. O SisTer Nexo já
concentra gestão científica e governança operacional. O repositório
`cpp/sister_compras` concentra necessidades, requisitos, alternativas,
cotações e decisões técnicas de aquisição.

Manter projetos em ambos sem contrato produziria cadastros concorrentes. Absorver
compras no banco do Nexo eliminaria a autonomia de um contexto com regras,
aprovações, dados financeiros e ciclo de vida próprios.

## Decisão

O SisTer Nexo é a autoridade operacional para:

- portfólio e identidade dos projetos;
- estrutura de pesquisa, ações e atividades;
- responsáveis, cronogramas e estados de execução;
- evidências, produtos, publicações e rastreabilidade científica.

Compras permanece um subsistema e banco autônomos. Ele recebe referências
imutáveis de projeto, ação ou atividade e é autoridade para:

- necessidades e requisitos;
- alternativas, fornecedores e observações de preço;
- pareceres e decisões humanas de aquisição;
- atendimento, entrega e histórico do recurso adquirido.

`Nexo-Compras` é o nome de produto adotado para explicitar essa relação. O
identificador técnico continua `sister_compras` para preservar contratos,
histórico e compatibilidade.

Nenhum dos dois contextos compartilha tabelas, credenciais ou volumes. A
integração usa APIs contratadas, referências estáveis, proveniência e a
identidade originada no SisTer e encaminhada pelo Nexo.

## Implementação

1. contrato `nexo-compras.integration/1.0.0`;
2. rota aninhada alvo `/integrations/nexo/compras/`, não promovida na `v0.2.7`;
3. fronteira assinada SisTer–Nexo e proxy contratual Nexo–Compras, sujeito a
   gate específico antes da ativação;
4. referências `project_id`, `research_activity_id`, `activity_id` e `need_id`;
5. PostgreSQL independente do Compras em `55440`;
6. migração preservada com caminho de rollback.

## Consequências

- o SisTer Core continua catálogo, autenticação e convergência, não gestor de
  projetos nem sistema de compras;
- o Nexo ganha papel explícito na gestão de projetos e ações de pesquisa;
- aquisições podem ser rastreadas até a atividade que justificou a necessidade;
- dados comerciais, cotações e pareceres permanecem restritos ao Compras;
- indisponibilidade do Compras não pode corromper nem bloquear registros
  científicos do Nexo;
- a indisponibilidade do Compras degrada somente seu contexto no Nexo.
