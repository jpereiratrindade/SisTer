# Integração SisTer Nexo

O SisTer Nexo é o subsistema federado de governança operacional, gestão
científica, projetos, ações, atividades, evidências, publicações e
rastreabilidade.

## Papel no ecossistema

O Nexo é a autoridade operacional para o portfólio de projetos e para a
estrutura que conecta objetivos científicos, ações, atividades, responsáveis,
cronogramas, evidências e produtos. O SisTer Core mantém catálogo,
autenticação e convergência; não replica a gestão interna dos projetos.

Contextos especializados podem referenciar projetos e atividades do Nexo por
contrato. O primeiro candidato é `sister_compras`, que pode evoluir para a
identidade de produto **Nexo-Compras**. Compras continuará responsável por
necessidades, requisitos, alternativas, cotações e decisões de aquisição em
banco próprio.

## Contrato

- identificador: `sister_nexo`;
- contrato: `sister-nexo.integration/1.0.0`;
- origem local: `http://127.0.0.1:8015`;
- saúde sanitizada: `/api/health`;
- acesso: proxy autenticado em `/integrations/nexo/`;
- PostgreSQL: propriedade exclusiva do Nexo em `127.0.0.1:55439`.

O SisTer não acessa tabelas, credenciais, conversas, anexos, embeddings ou
auditoria bruta. Produtos agregados só podem atravessar a fronteira quando
previstos por contrato, com proveniência e classificação.

## Operação

O orquestrador pode iniciar `./scripts/run.sh` no repositório do Nexo. A
indisponibilidade é degradável e não impede a subida do Core. O Nexo exige
configuração local `.env`, que não é criada nem armazenada pelo SisTer.

## Evolução coordenada

A fronteira e as condições para integrar compras estão em
[`NEXO_COMPRAS.md`](./NEXO_COMPRAS.md) e na
[`ADR-0007`](../adr/ADR-0007-nexo-research-operations-and-procurement.md).
Essa documentação não ativa o Compras nem aprova ainda sua renomeação.
