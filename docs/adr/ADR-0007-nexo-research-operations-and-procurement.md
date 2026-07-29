# ADR-0007 — Nexo, operações de pesquisa e fronteira de compras

- Estado: aceito para a fronteira do Nexo; nome `Nexo-Compras` em avaliação
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

`Nexo-Compras` é o nome candidato para explicitar essa relação. A renomeação só
ocorrerá com contrato versionado, plano de migração de identidade e aprovação
específica; até lá, o identificador continua `sister_compras`.

Nenhum dos dois contextos compartilha tabelas, credenciais ou volumes. A
integração usa APIs ou pacotes contratados, referências estáveis, proveniência
e autorização do SisTer.

## Sequência de integração

1. consolidar e versionar a documentação e o estado atual dos repositórios;
2. corrigir a colisão da porta PostgreSQL `55435` com o ambiente de teste do
   SisTer;
3. alinhar a versão do contrato do Compras com a aplicação `0.4.0`;
4. definir referências de `project_id`, `research_activity_id`, `activity_id`
   e `need_id`, além de regras para atualização e arquivamento;
5. implementar saúde sanitizada, identidade federada e proxy autenticado;
6. validar migração de dados e somente então habilitar `ensure-running`;
7. decidir e executar, ou rejeitar, a mudança de nome para `Nexo-Compras`.

## Consequências

- o SisTer Core continua catálogo, autenticação e convergência, não gestor de
  projetos nem sistema de compras;
- o Nexo ganha papel explícito na gestão de projetos e ações de pesquisa;
- aquisições podem ser rastreadas até a atividade que justificou a necessidade;
- dados comerciais, cotações e pareceres permanecem restritos ao Compras;
- indisponibilidade do Compras não pode corromper nem bloquear registros
  científicos do Nexo;
- integração operacional não será ativada enquanto os impedimentos de porta,
  contrato, identidade e migração permanecerem.
