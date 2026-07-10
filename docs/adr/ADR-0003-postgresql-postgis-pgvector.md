# ADR-0003: PostgreSQL, PostGIS e pgvector

## Status

Aceita

## Contexto

O SisTer precisa sustentar dados territoriais, evidencias, proveniencia, diagnosticos tecnicos e conhecimento derivado de integracoes entre sistemas federados. A camada inicial em arquivos e suficiente para prototipagem, mas nao resolve bem consultas espaciais, concorrencia, auditoria operacional, persistencia compartilhada e analises vetoriais.

## Decisao

Adotar PostgreSQL como banco operacional planejado do SisTer, com:

- PostGIS para objetos territoriais, geometrias, camadas, areas, campanhas e consultas espaciais;
- pgvector para embeddings, busca por similaridade, recuperacao semantica, deduplicacao assistida e aproximacao entre artefatos de conhecimento;
- modo arquivo/local preservado para desenvolvimento, demonstracao e ambientes offline simples.

## Consequencias

- O modelo de persistencia passa a distinguir dados publicos, restritos e privados.
- Geometrias e embeddings devem carregar proveniencia e politica de exposicao.
- O C++ core deve evoluir com uma porta de persistencia, evitando acoplamento direto do dominio a lib especifica de PostgreSQL.
- A interface deve consumir diagnosticos e resultados agregados, nao expor dados sensiveis brutos por padrao.
