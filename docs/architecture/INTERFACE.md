# Interface SisTer

## Objetivo

A interface inicial do SisTer existe para validar a leitura federativa da plataforma:

- quais sistemas participam;
- quais contratos sao reconhecidos;
- quais evidencias sustentam os dados;
- quais resultados de integracao ja existem;
- qual e o estado tecnico dos servicos que suportam as entregas.

Ela nao substitui os sistemas federados. MorfoCampo, DroneOps, CampoNode e futuros modulos continuam autonomos.

## Identidade visual

A identidade inicial segue a linguagem do `Radar-Sister Resiliencia`:

- topo horizontal institucional;
- azul escuro como estrutura;
- teal como acento de acao e destaque;
- cards brancos com bordas suaves;
- metricas compactas;
- dashboard objetivo;
- rodape institucional.

O rodape explicita tres compromissos:

- governanca: ADR, DDD, DAI, politicas e evidencias;
- LGPD: minimizacao, finalidade, rastreabilidade e controle de acesso;
- seguranca: proveniencia, checksum, auditoria, permissao e revisao proporcional ao risco.

## Navegacao

### Home

Apresenta:

- indicadores de sistemas, contratos, evidencias e conformidade;
- cards com informacao minima dos sistemas;
- barras de resultado de integracao;
- mapa territorial sintetico.

### Integracao

Representa a funcao de `Integracao e transformacao de conhecimento`.

Responsabilidades:

- ingerir manifestos, pacotes CampoSync, evidencias e logs;
- validar contrato, schema, proveniencia minima e checksum;
- transformar dados federados em objetos territoriais comuns;
- registrar artefatos de conhecimento produzidos pela integracao.

### Diagnostico

Representa a funcao de `Sintese tecnica e diagnostico dos servicos`.

Responsabilidades:

- dar transparencia ao status tecnico dos servicos;
- sinalizar prontidao operacional;
- expor riscos e pendencias;
- acompanhar governanca, LGPD e seguranca.

### Contratos

Exibe os contratos reconhecidos como fonte de verdade da integracao.

### Evidencias

Exibe eventos e referencias que sustentam proveniencia e auditabilidade.

## Estado atual

A interface esta em `web/` e usa dados demonstrativos embutidos em `web/app.js`.

Execucao local:

```bash
python3 -m http.server 8000 -d web
```

Acesso:

```text
http://localhost:8000
```

## Proximos incrementos

1. Exportar dados do `sister_core` para JSON consumido pela interface.
2. Adicionar API local para contratos, sistemas, evidencias e diagnosticos.
3. Persistir resultados de integracao e diagnostico.
4. Conectar validacao real de CampoSync aos dashboards.
5. Criar criterios formais para status operacional, LGPD e seguranca.
