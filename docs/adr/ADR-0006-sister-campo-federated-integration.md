# ADR-0006: SisTer-Campo como sistema federado de integracao

## Status

Aceita

## Contexto

Sistemas cientificos como o MorfoCampo operam de forma autonoma e offline. O
SisTer precisa receber dados de campo sem absorver o runtime cientifico, sem
compartilhar bancos e sem depender exclusivamente de conectividade.

## Decisao

O SisTer-Campo e registrado como sistema federado com identidade,
API e PostgreSQL proprios. A integracao usa dois canais equivalentes:

- API local autenticada para transporte online;
- pacote CampoSync para transporte offline e reprocessavel.

Os dois canais transportam o contrato `camposync.package/1.0.0`. O
SisTer-Campo valida, registra, cura e preserva proveniencia antes de promover
dados ao SisTer. O SisTer continua autoridade de governanca e, quando houver
interface humana federada, de identidade. O MorfoCampo permanece produtor
autonomo; CampoNode permanece experimental.

## Consequencias

- nao ha banco compartilhado entre SisTer, SisTer-Campo e MorfoCampo;
- repeticoes sao detectadas por `package_id` e checksum;
- pacotes sao restritos e midia bruta e privada por padrao;
- a API nao cria um segundo modelo de dados: transporta o mesmo CampoSync;
- promocao, curadoria e identidade humana exigem trilha de auditoria.
