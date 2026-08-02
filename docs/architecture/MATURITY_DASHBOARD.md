# Centro de Engenharia do SisTer

O Centro de Engenharia do SisTer é a interface visível do
[SGE-SisTer](../governance/SGE_SISTER.md). Ele apresenta relatórios
sanitizados produzidos pelos gates sem executar comandos e sem recalcular
aprovações.

## Fluxo

```text
scripts e testes -> verificador -> status JSON -> API admin -> painel
```

O verificador (`scripts/maturity/evaluator.py`) avalia uma execução usando
o Motor Declarativo. O histórico automático é produzido pelo comando
`scripts/sge maturity publish`, que arquiva cada status válido em
`.run/maturity/history/` e atualiza `.run/maturity/history/index.json`.

`scripts/sge` é a única interface operacional suportada. Os arquivos em
`scripts/maturity/` são implementações internas, não comandos alternativos.
A CLI resolve o engine explicitamente: `compare` para `sister-core` e
`declarative` para componentes federados, salvo quando `--engine` é informado.

## Visões

A tela combina leituras operacionais e executivas sobre a mesma atestação:

- síntese executiva do gate avaliado, próximo objetivo, bloqueios,
  advertências e confiança;
- escopo explícito da evidência: componente avaliado, gate, engine SGE,
  governança e impacto na promoção;
- pipeline Pré-Alfa, Alfa, Beta, Gama e Produção;
- catálogo de checks disponíveis nos perfis versionados;
- bloqueadores e proveniência;
- saúde da engenharia por dimensão derivada dos checks;
- **componentes do ecossistema federado** (Core, Nexo, Clima, etc.) com
  resultado técnico e modo de governança separados visualmente;
- árvore de decisão do gate avaliado;
- evidências por estágio;
- resultados da suíte geral de qualidade, com estado, comando, duração e código
  de saída de cada grupo de testes;
- histórico recente de execuções.
- guia interno explicando SisTer Core, componentes federados, engines,
  testes disponíveis, evidências executadas e suíte geral de qualidade.

As porcentagens e agrupamentos são derivados no navegador a partir dos checks
publicados. Eles ajudam a leitura, mas a decisão formal continua sendo o
`result`, os `blockers` e os estados produzidos pelo verificador.

## Separação visual: Avaliação técnica × Governança

O painel distingue explicitamente dois conceitos:

| Conceito | Badge | Semântica |
|---|---|---|
| Avaliação técnica | Verde/Vermelho/Amarelo | Resultado dos checks do estágio avaliado |
| Modo de governança | Cinza neutro (`SHADOW`) | Se o componente tem autoridade sobre promoções |

Um componente pode ter **Avaliação técnica: PASS** e **Governança: SHADOW**
ao mesmo tempo — isso significa que o ambiente técnico está sadio, mas que o
componente está em modo piloto e não influencia promoções do Core.

## Engines e modos de governança

O engine determina como a maturidade é verificada; o modo de governança
determina que autoridade o resultado possui.

| Conceito | Opções | Efeito |
|---|---|---|
| Engine | `compare`, `declarative`, `legacy` | Define como os critérios são executados |
| Governança | `shadow`, `governed` | Define se o resultado pode bloquear uma promoção |

Durante a transição, `compare` é o padrão porque executa `legacy` e
`declarative` e detecta divergências. `declarative` é o motor de destino.
`legacy` permanece como diagnóstico temporário.

`shadow` observa sem bloquear; `governed` pode bloquear somente no escopo
declarado. A passagem de `shadow` para `governed` exige maturidade técnica,
criticidade arquitetural e responsabilidade operacional formal.

Regra operacional mínima:

- `compare` divergiu: executar `legacy` e `declarative` isoladamente, comparar evidências e registrar a decisão.
- `shadow` falhou: registrar, alertar e acompanhar sem bloquear fora do escopo.
- `governed` falhou: bloquear o escopo afetado, preservar evidências e corrigir ou aprovar exceção formal.

Para critérios, impactos operacionais e procedimentos detalhados, consulte
[Engines de verificação e modos de governança](./sgr/verification-engines-and-governance-modes.md).

## Publicação

Fluxo completo recomendado:

```bash
./scripts/sge verify
```

Ele executa a suíte geral de qualidade e publica a maturidade de todos os
componentes localmente resolvíveis. Para operar apenas a maturidade:

```bash
./scripts/sge maturity publish
./scripts/sge maturity publish-all pre-alpha
```

Sem argumento, o script avalia o projeto principal (`sister-core`) e infere o estágio a partir de `.sister/status.yml`.
Também é possível informar explicitamente o estágio:

```bash
./scripts/sge maturity publish pre-alpha
./scripts/sge maturity publish pre-alpha --engine compare
```

### Componentes e Pilotos (Modo Shadow)

Para avaliar um subsistema ou componente externo, forneça o ID do componente e o caminho raiz do respectivo repositório:

```bash
./scripts/sge maturity publish pre-alpha \
  --component sister-nexo \
  --component-root /caminho/para/o/repo/do/nexo
```

#### Exemplo com Sister-Clima (Python/Streamlit)

```bash
./scripts/sge maturity publish pre-alpha \
  --component sister-clima \
  --component-root /caminho/para/o/repo/do/clima
```

O Motor Declarativo suporta componentes em qualquer tecnologia via scripts delegados.
Para componentes Python que usam `venv`, os scripts de CI detectam automaticamente
o interpretador correto em `venv/bin/python` ou `.venv/bin/python`, garantindo
que dependências como `h3`, `shapely` etc. sejam encontradas sem alterar o ambiente
do sistema.

### Tipos de checks suportados

| Tipo | Descrição |
|---|---|
| `file_exists` | Verifica a existência de um arquivo específico |
| `any_file_exists` | Verifica se ao menos um arquivo de uma lista existe (útil para entrypoints alternativos) |
| `directory_exists` | Verifica a existência de um diretório |
| `regex_match` | Verifica se algum arquivo corresponde a um padrão de nome |
| `regex_present` | Verifica se um padrão está presente no conteúdo de arquivo(s) |
| `script` | Executa um script delegado registrado no perfil do componente |
| `min_count` | Verifica contagem mínima de arquivos em diretório |
| `no_tracked_secrets` | Verifica ausência de arquivos suspeitos no repositório |
| `git_repo` | Verifica se o diretório é um repositório Git válido |
| `git_clean` | Verifica se o repositório está limpo (não bloqueante fora do modo certify) |
| `approval` | Verifica presença de aprovação formal em arquivo YAML |

### Arquivos Locais

- `.run/maturity/latest.json`: estado da última execução do Core (consumido pela UI);
- `.run/maturity/components.json`: índice federado com as últimas execuções de todos os componentes;
- `.run/maturity/catalog.json`: catálogo de checks disponíveis nos perfis versionados;
- `.run/maturity/quality.json`: qualidade da árvore, anterior à inicialização e
  independente da disponibilidade do ecossistema;
- `.run/maturity/run-all-status.json`: resultado integrado do perfil, com banco,
  prontidão, smoke e ecossistema (`PASS`, `PASS_WITH_DEGRADATION` ou `BLOCKED`);
- `.run/maturity/subsystems.json`: diagnóstico estruturado da última seleção de
  subsistemas, incluindo fase, obrigatoriedade, código de saída e log;
- `.run/maturity/components/<id>/latest.json`: estado consolidado de um componente específico;
- `.run/maturity/components/<id>/history/*.json`: atestações históricas do componente;
- `build/maturity/`: relatórios Markdown tradicionais.

Esses diretórios não são versionados. A publicação preserva o código de saída
do gate, portanto uma execução reprovada ainda produz evidência e retorna erro.

## Acesso

- página: `/admin/maturity`;
- status: `GET /api/admin/maturity/latest`;
- componentes (ecossistema): `GET /api/admin/maturity/components`;
- catálogo de checks: `GET /api/admin/maturity/catalog`;
- suíte geral de qualidade: `GET /api/admin/maturity/quality`;
- histórico: `GET /api/admin/maturity/history`.

As rotas exigem sessão administrativa e respondem com `Cache-Control: no-store`.
Não existe endpoint para executar o gate.

## Diagnóstico

- `404`: nenhuma execução foi publicada;
- `503`: evidência ausente de schema conhecido, ilegível ou acima do limite;
- `401`: sessão ausente ou expirada;
- `403`: conta autenticada sem permissão administrativa.
