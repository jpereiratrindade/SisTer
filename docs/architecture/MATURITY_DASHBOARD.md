# Centro de Engenharia do SisTer

O Centro de Engenharia do SisTer é a interface visível do
[SGE-SisTer](../governance/SGE_SISTER.md). Ele apresenta relatórios
sanitizados produzidos pelos gates sem executar comandos e sem recalcular
aprovações.

## Fluxo

```text
scripts e testes -> verificador -> status JSON -> API admin -> painel
```

O verificador (`scripts/verify-sister-maturity.sh`) avalia uma execução. O
histórico automático é produzido pelo wrapper de publicação
`scripts/maturity/run-and-publish.sh`, que arquiva cada status válido em
`.run/maturity/history/` e atualiza `.run/maturity/history/index.json`.

## Visões

A tela combina leituras operacionais e executivas sobre a mesma atestação:

- síntese executiva do gate avaliado, próximo objetivo, bloqueios,
  advertências e confiança;
- pipeline Pré-Alfa, Alfa, Beta, Gama e Produção;
- bloqueadores e proveniência;
- saúde da engenharia por dimensão derivada dos checks;
- leitura inicial por plataforma e subsistemas;
- árvore de decisão do gate avaliado;
- evidências por estágio;
- histórico recente de execuções.

As porcentagens e agrupamentos são derivados no navegador a partir dos checks
publicados. Eles ajudam a leitura, mas a decisão formal continua sendo o
`result`, os `blockers` e os estados produzidos pelo verificador.

## Publicação

```bash
./scripts/maturity/run-and-publish.sh
```

Sem argumento, o script avalia o projeto principal (`sister-core`) e infere o estágio a partir de `.sister/status.yml`.
Também é possível informar explicitamente o estágio:

```bash
./scripts/maturity/run-and-publish.sh pre-alpha
```

### Componentes e Pilotos (Modo Shadow)

Para avaliar um subsistema ou componente externo (ex: Nexo), forneça o ID do componente e o caminho raiz do repositório respectivo:

```bash
./scripts/maturity/run-and-publish.sh pre-alpha \
  --component sister-nexo \
  --component-root /caminho/para/o/repo/do/nexo
```

O orquestrador utilizará o Motor Declarativo sob o perfil respectivo (ex: `sister-nexo.yaml`). O resultado será projetado no dashboard mantendo o isolamento de métricas.

### Arquivos Locais

- `.run/maturity/latest.json`: estado da última execução (consumido imediatamente pela UI);
- `.run/maturity/components.json`: índice federado com as últimas execuções de todos os componentes testados;
- `.run/maturity/components/<id>/latest.json`: estado consolidado de um componente específico;
- `.run/maturity/components/<id>/history/*.json`: atestações históricas do componente;
- `build/maturity/`: relatórios Markdown tradicionais.

Esses diretórios não são versionados. A publicação preserva o código de saída
do gate, portanto uma execução reprovada ainda produz evidência e retorna erro.

## Acesso

- página: `/admin/maturity`;
- status: `GET /api/admin/maturity/latest`;
- componentes (ecossistema): `GET /api/admin/maturity/components`;
- histórico: `GET /api/admin/maturity/history`.

As rotas exigem sessão administrativa e respondem com `Cache-Control: no-store`.
Não existe endpoint para executar o gate.

## Diagnóstico

- `404`: nenhuma execução foi publicada;
- `503`: evidência ausente de schema conhecido, ilegível ou acima do limite;
- `401`: sessão ausente ou expirada;
- `403`: conta autenticada sem permissão administrativa.
