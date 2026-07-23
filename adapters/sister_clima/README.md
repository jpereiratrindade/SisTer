# Adaptador Sister-Clima

O Sister-Clima permanece um sistema autonomo. Nesta fase, o SisTer o integra
por descoberta de manifesto, link para a plataforma local e importacao
controlada de arquivos exportados.

## Contrato reconhecido

- manifesto de referencia: `examples/sister_clima_manifest_example.json`;
- manifesto mantido pela origem:
  `python/Sister-Clima/contracts/system_manifest.json`;
- contrato: `sister-contracts/0.1.0`;
- identificador: `sister_clima`;
- plataforma local: `http://127.0.0.1:8501`;
- saude Streamlit: `http://127.0.0.1:8501/_stcore/health`.

## Fronteira de dados

O SisTer pode receber indicadores climaticos revisados, camadas espaciais
explicitamente exportadas, cobertura temporal e metadados de proveniencia.
Respostas brutas das APIs, parametros de sessao, configuracao de rede e logs
permanecem no Sister-Clima.

Arquivos derivados do Open-Meteo conservam a atribuicao e as restricoes da
fonte. O SisTer nao deve promover indicadores ou camadas sem validacao de
schema, proveniencia, operador responsavel e referencia espacial.

## Estado da integracao

O catalogo e o endpoint publico `/api/systems` anunciam o Sister-Clima e abrem
sua interface de origem. A ingestao automatica dos arquivos exportados ainda
nao esta implementada; ate la, `file_import` representa uma fronteira
contratual para importacao controlada, nao sincronizacao automatica.
