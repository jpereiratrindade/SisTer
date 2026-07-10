# ADR-0002: Interface de convergencia e diagnostico

## Status

Aceita

## Contexto

O SisTer precisa tornar visivel a proposta federativa antes de possuir servidor HTTP completo, persistencia SQLite ou sincronizacao distribuida. A interface deve mostrar sistemas federados, contratos, evidencias, proveniencia e resultados de integracao sem deslocar o centro arquitetural para uma aplicacao web monolitica.

Tambem ha interesse em alinhar a identidade visual ao `Radar-Sister Resiliencia`, mantendo continuidade institucional entre os projetos.

## Decisao

Criar uma primeira interface estatica em `web/`, com:

- barra superior horizontal;
- home com cards classicos de sistemas;
- dashboard de resultados de integracao;
- area de integracao e transformacao de conhecimento;
- area de sintese tecnica e diagnostico dos servicos;
- contratos e evidencias em secoes dedicadas;
- rodape com referencias a governanca, LGPD e seguranca.

A interface usa dados demonstrativos embutidos em `web/app.js` ate que exista API local ou exportacao JSON produzida pelo `sister_core`.

## Consequencias

- A proposta pode ser validada visualmente sem introduzir dependencias de frontend ou backend.
- O produto passa a distinguir a funcao epistemica de integracao/conhecimento da funcao operacional de diagnostico/transparencia.
- Os proximos incrementos devem substituir dados embutidos por dados gerados pelo core, mantendo contratos como fonte de verdade.
