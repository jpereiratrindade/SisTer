# Integração SisTer Nexo

O SisTer Nexo é o subsistema federado de governança operacional, gestão
científica, projetos, ações, atividades, evidências, publicações e
rastreabilidade.

## Papel no ecossistema

O Nexo é a autoridade operacional para o portfólio de projetos e para a
estrutura que conecta objetivos científicos, ações, atividades, responsáveis,
cronogramas, evidências e produtos. O SisTer Core mantém catálogo,
autenticação e convergência; não replica a gestão interna dos projetos.

O **Nexo-Compras** referencia projetos e atividades do Nexo por contrato.
Compras continua responsável por necessidades, requisitos, alternativas,
cotações e decisões de aquisição em banco próprio. A relação é
`SisTer → Nexo → Nexo-Compras`: não existe contrato operacional direto entre
SisTer e Compras.

## Contrato

- identificador: `sister_nexo`;
- contrato: `sister-nexo.integration/1.0.0`;
- origem local: `http://127.0.0.1:8015`;
- saúde sanitizada: `/api/health`;
- acesso: proxy autenticado em `/integrations/nexo/`;
- contexto Compras: proxy do Nexo em `/integrations/nexo/compras/`;
- PostgreSQL: propriedade exclusiva do Nexo em `127.0.0.1:55439`.

O SisTer não acessa tabelas, credenciais, conversas, anexos, embeddings ou
auditoria bruta. Produtos agregados só podem atravessar a fronteira quando
previstos por contrato, com proveniência e classificação.

## Portfólio multiprojeto

O Nexo possui a seção própria **Projetos** e mantém `nexo_projects` como
Aggregate raiz. O projeto Resiliência é o registro fundador migrado, não um
contexto implícito da plataforma. Novos projetos podem registrar nome, sigla,
instituição líder, descrição, período e estado.

O campo `name` é o título oficial e pode ser extenso. O campo `short_name` é o
rótulo compacto usado em navegação, seletores e integrações visuais, com
`project_id` como fallback. O título integral permanece preservado nos detalhes
e contratos.

Desafios e atividades exigem `project_id` explícito, e atividades científicas
só podem referenciar desafios do mesmo projeto. Equipe, autorização,
informações de compras e vínculos externos são resolvidos pelo projeto
correlacionado. O SisTer autentica e encaminha a identidade, mas não cria nem
edita projetos do Nexo.

## Operação

O orquestrador pode iniciar `./scripts/run.sh` no repositório do Nexo. A
indisponibilidade é degradável e não impede a subida do Core. O Nexo exige
configuração local `.env`, que não é criada nem armazenada pelo SisTer.

## Fronteira Nexo-Compras

A fronteira implementada está em
[`NEXO_COMPRAS.md`](./NEXO_COMPRAS.md) e na
[`ADR-0007`](../adr/ADR-0007-nexo-research-operations-and-procurement.md).
O orquestrador raiz pode garantir a disponibilidade do processo, mas isso não
altera a propriedade do contrato: o Compras integra-se ao Nexo.
