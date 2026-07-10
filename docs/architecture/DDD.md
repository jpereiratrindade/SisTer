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
- Regra: o SisTer conhece o contrato entregue, nao a implementacao interna do sistema.

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

## Ontologia Minima

- O que existe: sistemas federados, contratos, pacotes, evidencias, objetos territoriais, visoes de convergencia.
- Como se relacionam: sistemas produzem pacotes; pacotes seguem contratos; evidencias sustentam objetos; proveniencia conecta origem e validade.
- O que e valido: contratos versionados, schema aprovado, checksum verificavel, proveniencia minima.
- Como identificar: ids canonicos por sistema, contrato, pacote, evidencia e objeto territorial.
