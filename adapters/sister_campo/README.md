# Adaptador SisTer-Campo

O SisTer-Campo e um sistema federado autonomo e a fronteira de integracao dos
sistemas cientificos de campo. Ele possui API e PostgreSQL proprios; nenhum
banco e compartilhado com o SisTer.

## Canais contratados

- `CampoSync`: pacote ZIP versionado para operacao offline, reprocessamento e
  auditoria;
- API local: transporte autenticado do mesmo pacote CampoSync;
- promocao ao SisTer: somente depois de validacao e curadoria, preservando
  pacote de origem, checksum e relatorio.

O contrato canonico e `contracts/camposync_package.schema.json`, versao `1.0.0`.
O endpoint local reservado do SisTer-Campo e `127.0.0.1:8013`. Conteudo de
pacotes e restrito; midia bruta, identidade de operador e auditoria sao
privados por padrao.

O MorfoCampo permanece produtor autonomo e nao e iniciado pelo SisTer-Campo. O
CampoNode permanece projeto experimental e nao representa a identidade do
SisTer-Campo.
