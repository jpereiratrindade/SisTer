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

A interface está em `web/` e consome a API do `sisterd`. Sistemas, contratos,
evidências e diagnósticos são servidos por endpoints JSON lidos do PostgreSQL
quando `SISTER_DATABASE_URL` está definido. Sem banco, o servidor responde com
dados de fallback sem interrupção de serviço.

Execucao local:

```bash
python3 -m http.server 8000 -d web
```

Acesso:

```text
http://localhost:8000
```

## Proximos incrementos

1. Alimentar `/api/diagnostics` com coletor real conectado ao banco e aos subsistemas.
2. Persistir resultados de integracao e pacotes CampoSync recebidos.
3. Conectar validacao real de CampoSync aos dashboards.
4. Criar criterios formais para status operacional, LGPD e seguranca.
5. Adicionar objetos territoriais persistidos (PostGIS).
