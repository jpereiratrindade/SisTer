# DDD - SisTer

## Objetivo

Definir o modelo de dominio do SisTer como plataforma federativa de convergencia territorial orientada por contratos.

## Contextos Delimitados

### 1. Contratos de Integracao

Responsavel por schemas, manifestos, versoes e compatibilidade.

- Entidade: `Contract`
- Entidade: `SystemManifest`
- Regra: importacao federada exige contrato versionado e validacao de schema.

### 2. Registro de Sistemas Federados

Responsavel por catalogar sistemas autonomos que conversam com o SisTer.

- Entidade: `FederatedSystem`
- Value Object: `SystemAccess`
- Value Object: `SharingPolicy`
- Regra: o SisTer conhece o contrato entregue, nao a implementacao interna do sistema.
- Regra: cada sistema deve declarar o que compartilha com o SisTer, o que permanece nativo da propria plataforma e qual link de acesso deve ser exibido quando aplicavel.

### 3. Ingestao CampoSync

Responsavel por receber pacotes offline ou locais de sincronizacao.

- Entidade: `CampoSyncPackage`
- Regra: pacote importado precisa de manifesto, checksum, proveniencia e relatorio de validacao.

### 4. Evidencia e Proveniencia

Responsavel por vincular objetos territoriais a fonte, autoria, tempo, contrato e evidencia.

- Entidade: `Evidence`
- Entidade: `ProvenanceRecord`
- Regra: dado territorial sem proveniencia minima nao deve ser promovido para catalogo confiavel.

### 5. Catalogo Territorial

Responsavel por leitura, cruzamento e interpretacao territorial.

- Entidade: `TerritorialObject`
- Value Object: `SpatialContext`
- Regra: objetos precisam de identidade, validade, contexto espacial quando aplicavel e origem rastreavel.

### 6. Interface de Convergencia

Responsavel por expor leitura comum de sistemas, contratos, evidencias, mapa e proveniencia.

- Entidade de leitura: `ConvergenceView`
- Regra: a interface nao substitui os sistemas federados; ela apresenta contratos reconhecidos e objetos interpretaveis pelo SisTer.

### 7. Integracao e Transformacao de Conhecimento

Responsavel por transformar dados federados em conhecimento territorial comum.

- Entidade: `IntegrationRun`
- Entidade: `KnowledgeArtifact`
- Value Object: `DikwRole`
- Regra: toda transformacao precisa preservar contrato de origem, evidencias usadas, criterio de validade e resultado produzido.
- Regra: a informacao ofertada pelo sistema federado e recebida pelo SisTer como dado; o SisTer pode transforma-la em informacao integrada, conhecimento territorial e apoio a sabedoria decisoria.

### 8. Sintese Tecnica e Diagnostico dos Servicos

Responsavel por sintetizar o estado tecnico dos servicos que sustentam as entregas do SisTer.

- Entidade: `ServiceDiagnostic`
- Entidade: `OperationalStatus`
- Value Object: `InfrastructureMetric`
- Regra: diagnosticos devem distinguir saude tecnica, conformidade contratual, riscos de seguranca, sinais LGPD e governanca operacional.
- Regra: cards de sistemas podem exibir metricas de infraestrutura como disponibilidade, resposta/sincronizacao, uso de armazenamento e ultima verificacao, desde que a origem da metrica seja rastreavel.

### 9. Persistencia Territorial e Vetorial

Responsavel por persistir dados operacionais, geoespaciais e vetoriais.

- Entidade: `SpatialLayer`
- Entidade: `VectorEmbedding`
- Entidade: `PersistencePolicy`
- Regra: geometrias, embeddings e artefatos derivados precisam carregar proveniencia, finalidade e escopo de exposicao.

### 10. Escopo Publico e Privado

Responsavel por classificar o que pode ser publicado, compartilhado internamente ou protegido.

- Value Object: `PublicScope`
- Valores: `public`, `restricted`, `private`
- Regra: quando houver duvida, classificar como `private` ate revisao humana.
- Regra: temas sensiveis devem ser declarados no manifesto do sistema e nao devem ser inferidos apenas pela interface.

## Ontologia Minima

- O que existe: sistemas federados, acessos diretos, politicas de compartilhamento, contratos, pacotes, evidencias, objetos territoriais, visoes de convergencia, execucoes de integracao, artefatos de conhecimento, diagnosticos de servico, geometrias, embeddings e politicas de exposicao.
- Como se relacionam: sistemas produzem pacotes; pacotes seguem contratos; evidencias sustentam objetos; proveniencia conecta origem e validade; informacoes ofertadas por sistemas chegam ao SisTer como dados e podem ser transformadas em informacao, conhecimento e sabedoria.
- O que e valido: contratos versionados, schema aprovado, checksum verificavel, proveniencia minima, finalidade declarada e escopo de exposicao definido.
- Como identificar: ids canonicos por sistema, contrato, pacote, evidencia e objeto territorial.

## Sistemas integrantes iniciais

- `morfocampo`: sistema autonomo de campo.
- `droneops`: sistema autonomo de missao e evidencia geoespacial.
- `camponode`: infraestrutura local de operacao.
- `radar_sister_resiliencia`: sistema analitico de triagem, resiliencia, inteligencia territorial e governanca de dados.
