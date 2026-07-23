# ADR-0004: Integração de serviço com o Sister-Studio

## Status

Aceita

## Contexto

O SisTer precisa reconhecer o Sister-Studio sem absorver sua implementação,
identidades ou acervo audiovisual. Voz, texto e mídia podem conter dados
pessoais, dados de alto risco, direitos autorais e segredos de criação.
Disponibilidade e formatos, por outro lado, são úteis ao diagnóstico e ao
planejamento federativo.

## Decisão

Adotar o contrato versionado `sister-studio.integration/1.0.0` com uma primeira
fase estritamente somente leitura:

- catálogo de capacidades e formatos;
- saúde sanitizada de composição, voz e vídeo;
- HTTPS com validação do certificado;
- token de serviço em arquivo de execução, nunca versionado;
- acesso no SisTer restrito a administrador e respostas sem cache;
- negação por padrão para conteúdo, identidade e artefatos.

O Sister-Studio permanece proprietário das operações criativas e dos dados. O
SisTer consome a descrição contratada, conforme o contexto de Registro de
Sistemas Federados e de Síntese Técnica. Falhas do adaptador são transformadas
em códigos seguros, sem transportar detalhes internos.

## Consequências

- O SisTer pode descobrir interoperabilidade e disponibilidade reais.
- A integração funciona sem banco compartilhado e sem sessão de usuário
  compartilhada.
- Trabalhos delegados e troca de artefatos exigirão nova decisão, contratos
  próprios e governança de tratamento.
- Métricas futuras precisam de limiar de divulgação e avaliação de
  reidentificação; agregação isolada não prova anonimização.
- Os papéis LGPD serão definidos por implantação e finalidade, não pelo código.
