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
o Motor Declarativo. O histórico automático é produzido pelo wrapper de
publicação `scripts/maturity/run-and-publish.sh`, que arquiva cada status
válido em `.run/maturity/history/` e atualiza `.run/maturity/history/index.json`.

## Visões

A tela combina leituras operacionais e executivas sobre a mesma atestação:

- síntese executiva do gate avaliado, próximo objetivo, bloqueios,
  advertências e confiança;
- pipeline Pré-Alfa, Alfa, Beta, Gama e Produção;
- bloqueadores e proveniência;
- saúde da engenharia por dimensão derivada dos checks;
- **componentes do ecossistema federado** (Core, Nexo, Clima, etc.) com
  resultado técnico e modo de governança separados visualmente;
- árvore de decisão do gate avaliado;
- evidências por estágio;
- histórico recente de execuções.

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

Para avaliar um subsistema ou componente externo, forneça o ID do componente e o caminho raiz do respectivo repositório:

```bash
./scripts/maturity/run-and-publish.sh pre-alpha \
  --component sister-nexo \
  --component-root /caminho/para/o/repo/do/nexo
```

#### Exemplo com Sister-Clima (Python/Streamlit)

```bash
./scripts/maturity/run-and-publish.sh pre-alpha \
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
