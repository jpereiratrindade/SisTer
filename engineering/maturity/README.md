# Módulo de Maturidade de Engenharia

Este módulo reúne o modelo, os perfis e as suites de checks usados pelo
SGE-SisTer para avaliar maturidade técnica de componentes do ecossistema.

Ele deixou de ser apenas um teste local do SisTer-Core. A forma atual já é um
módulo interno parametrizado por contratos:

```text
modelo -> perfil do componente -> suites de checks -> avaliador -> atestação JSON -> publicação -> Centro de Engenharia
```

## Fronteira

| Parte | Local | Papel |
|---|---|---|
| Modelo | `engineering/maturity/models/` | Define estágios como `pre-alpha`, `alpha`, `beta`, `gamma` e `production` |
| Perfil | `engineering/maturity/profiles/` | Declara componente, modo de governança, scripts e suites aplicáveis |
| Checks | `engineering/maturity/checks/` | Declaram critérios executáveis por estágio |
| Avaliador | `scripts/maturity/evaluator.py` | Executa perfis declarativos e produz `sister.maturity-status/1.0.0` |
| Publicador interno | `scripts/maturity/run-and-publish.sh` | Implementação chamada exclusivamente pela CLI SGE |
| CLI SGE | `scripts/sge` | Entrada operacional única para avaliação, publicação e validação |
| Contratos | `contracts/engineering/` e `contracts/maturity/` | Definem formatos de entrada e saída |

`scripts/verify-sister-maturity.sh` continua como compatibilidade do Core
durante a transição, mas o destino arquitetural é o avaliador declarativo em
`scripts/maturity/evaluator.py`.

## Uso rápido

Executar a verificação completa recomendada, combinando a suíte geral de
qualidade com a publicação de maturidade de todos os componentes resolvíveis:

```bash
./scripts/sge verify
```

Para usar um gate explícito em todos os componentes:

```bash
./scripts/sge verify alpha
```

`verify` continua até executar as duas camadas e retorna erro se qualidade ou
maturidade falharem. Componentes externos cuja raiz não esteja configurada são
informados como `SKIP`.

Avaliar e publicar o estágio inferido de `.sister/status.yml`:

```bash
./scripts/sge maturity publish
```

Avaliar e publicar um estágio específico do Core:

```bash
./scripts/sge maturity publish pre-alpha
./scripts/sge maturity publish alpha
```

Avaliar e publicar todos os componentes resolvíveis do ecossistema:

```bash
./scripts/sge maturity publish-all pre-alpha
```

`publish-all` percorre `engineering/maturity/ecosystem.yaml`. Componentes sem
perfil ou sem raiz local resolvível são registrados como `SKIP` no terminal e
continuam aparecendo no índice de componentes. Para componentes externos,
declare a raiz por variável de ambiente, por exemplo:

```bash
export SISTER_CLIMA_REPO=/caminho/para/sister-clima
export SISTER_NEXO_REPO=/caminho/para/sister-nexo
./scripts/sge maturity publish-all pre-alpha
```

Avaliar um componente federado em modo `shadow`:

```bash
./scripts/sge maturity publish pre-alpha \
  --component sister-clima \
  --component-root /caminho/para/sister-clima
```

Executar diretamente o motor declarativo, sem publicar histórico:

```bash
./scripts/sge maturity evaluate pre-alpha
./scripts/sge maturity evaluate pre-alpha --engine compare
```

Validar modelos, perfis e checks contra os contratos:

```bash
./scripts/sge maturity validate
```

Validar uma atestação JSON publicada:

```bash
./scripts/sge maturity validate --status-json .run/maturity/latest.json
```

Engines disponíveis:

| Engine | Escopo inicial | Uso |
|---|---|---|
| `legacy` | `sister-core` | Compatibilidade e diagnóstico do verificador histórico |
| `declarative` | Todos os componentes com perfil | Motor de destino baseado em YAML |
| `compare` | `sister-core` | Executa `legacy` e `declarative`, compara resultados e publica divergências |

Padrões quando `--engine` não é informado:

- `sister-core`: `compare`;
- componentes federados: `declarative`.

`compare` produz uma atestação própria. O bloco `evaluation.comparison`
registra `status`, `equivalent`, `engines_executed` e divergências
estruturadas. Divergência bloqueante retorna código `5`, diferente de
reprovação técnica do gate, que retorna código `1`.

Não execute os scripts de `scripts/maturity/` diretamente. Eles são detalhes de
implementação e podem mudar. A entrada operacional suportada é sempre
`./scripts/sge`. Para avaliar sem publicar:

```bash
./scripts/sge maturity evaluate pre-alpha
```

## Arquivos produzidos

O publicador escreve em `.run/maturity/`, que não é versionado:

- `.run/maturity/latest.json`: última atestação publicada para consumo da UI;
- `.run/maturity/components.json`: índice federado dos componentes avaliados;
- `.run/maturity/catalog.json`: catálogo dos checks disponíveis nos perfis versionados;
- `.run/maturity/components/<id>/latest.json`: última atestação do componente;
- `.run/maturity/components/<id>/history/*.json`: histórico do componente;
- `.run/maturity/components/<id>/history/index.json`: índice do histórico.

Relatórios Markdown tradicionais do Core continuam em `build/maturity/`.

## O que significa testar SisTer Core

`sister-core` é o perfil de maturidade do núcleo deste repositório. Ele cobre
o conjunto central que sustenta a plataforma: contratos, autenticação, sessão,
APIs administrativas, evidências, maturidade, integração dos adaptadores e o
serviço `sisterd`.

Testar `sister-core` não significa executar todos os subsistemas externos. A
execução do Core verifica se o núcleo e seus contratos estão aderentes ao gate.
Os perfis específicos de `sister-clima` e `sister-nexo` são candidatos em
quarentena. Eles preservam a avaliação independente, mas não são executados por
perfis oficiais do núcleo nem produzem autorização de integração.

## Testes disponíveis × testes executados

O SGE distingue duas leituras:

| Leitura | Fonte | Significado |
|---|---|---|
| Testes disponíveis | `.run/maturity/catalog.json` | Inventário dos checks declarados nos perfis versionados |
| Evidências executadas | `.run/maturity/latest.json` e histórico | Checks que rodaram na última atestação publicada |
| Qualidade | `.run/maturity/quality.json` | Resultado de build, CTest e validadores da última execução de `run_quality.sh` |
| Componentes | `.run/maturity/components.json` | Estado consolidado por componente federado |

O catálogo histórico de maturidade contém checks declarados para:

- `sister-core`;
- `sister-clima`;
- `sister-nexo`.

`sister-clima`, `sister-nexo`, `sister-campo` e `sister-studio` estão marcados
como `quarantined` no ecossistema de maturidade. Somente `sister-core` e a
referência normativa participam da validação operacional atual.

## Relação com outros testes do repositório

O módulo de maturidade não substitui a suíte geral de qualidade. O comando:

```bash
./scripts/run_quality.sh
```

executa build CMake, `ctest`, validações de contratos, governança, recursos
locais, testes Python e validação de shell scripts. Esses testes verificam a
saúde do repositório e das ferramentas. O SGE usa parte deles como evidência de
maturidade quando um perfil referencia scripts delegados. A execução publica
automaticamente `.run/maturity/quality.json`, exibido na aba `Qualidade` com o
estado, comando, duração e código de saída de cada grupo.

Lista atual da suíte geral:

```text
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
python3 scripts/validate_tool_contracts.py
python3 scripts/validate_governance_repo.py
python3 scripts/validate_local_resources.py
python3 scripts/maturity/validate-contracts.py
python3 -m unittest scripts/subsystems/test_ensure.py
python3 -m unittest discover -s tests/maturity -p 'test_*.py'
./scripts/validate_shell_scripts.sh
```

`legacy`, `declarative` e `compare` não são componentes. Eles são engines do
verificador SGE:

- `legacy`: executa o verificador histórico do Core;
- `declarative`: executa perfis e checks YAML;
- `compare`: executa `legacy` e `declarative`, compara os resultados e registra
  divergências estruturadas.

Portanto, eles entram na aba `SGE / Engines` do Centro de Engenharia. Já os
checks por componente entram em `Testes Disponíveis` e `Evidências Executadas`.

## Como ler o resultado

O resultado técnico fica em `result`, `summary`, `stages` e `checks`.

A autoridade de promoção fica em `promotion` e `evaluation`:

- `evaluation.engine`: engine usado, hoje `declarative` nas execuções diretas;
- `evaluation.evaluation_mode`: `shadow` ou `governed`;
- `evaluation.governance_authority`: se o componente possui autoridade de governança;
- `evaluation.promotion_enabled`: se a avaliação pode recomendar promoção ou bloqueio;
- `promotion.applicable`: se promoção se aplica ao componente;
- `promotion.recommendation`: `promote`, `block` ou `not_applicable`.

Um componente pode ter `result: FAIL` e `promotion.applicable: false` quando
está em `shadow`. Isso registra a falha sem bloquear a promoção global.

## Perfis

Um perfil mínimo declara o componente, o modelo, o modo de governança e as
suites de checks:

```yaml
schema: "sister.engineering.maturity-profile/1.0.0"
id: "meu-componente"
name: "Perfil de avaliação do meu componente"
component: "meu-componente"
model: "sister-sge"
evaluation_mode: "shadow"
governance_authority: false
promotion_enabled: false
scripts:
  ci.test:
    path: scripts/ci/test.sh
check_suites:
  - "engineering/maturity/checks/common/repository.yaml"
  - "engineering/maturity/checks/common/security-baseline.yaml"
  - "engineering/maturity/checks/meu-componente/pre-alpha-checks.yaml"
```

Regras:

- componentes novos entram em `shadow` até decisão arquitetural em contrário;
- `shadow` exige `governance_authority: false` e `promotion_enabled: false`;
- `promotion_enabled: true` exige `governance_authority: true`;
- promover de `shadow` para `governed` exige decisão formal e escopo declarado.

## Checks

Cada suite é uma lista YAML de checks. Exemplo:

```yaml
- schema: "sister.engineering.maturity-check/1.0.0"
  id: "unit-tests"
  stage: "pre-alpha"
  type: "script"
  mandatory: true
  description: "Testes automatizados executam com sucesso"
  script_ref: "ci.test"
  timeout_seconds: 300
```

Tipos suportados pelo avaliador atual:

| Tipo | Uso |
|---|---|
| `file_exists` | Exige arquivo específico |
| `any_file_exists` | Aceita uma entre várias opções de arquivo |
| `directory_exists` | Exige diretório |
| `regex_match` | Procura arquivo cujo caminho corresponda a regex |
| `regex_present` | Procura padrão no conteúdo de arquivo ou diretório |
| `script` | Executa script delegado declarado no perfil |
| `min_count` | Exige quantidade mínima de arquivos em diretório |
| `approval` | Exige arquivo com `status: approved` ou `status: aprovado` |
| `git_repo` | Exige repositório Git válido |
| `git_clean` | Avisa sobre worktree suja em modo check; bloqueia em `MODE=certify` |
| `stable_tag` | Exige tag semântica no commit atual |
| `signed_tag` | Exige tag assinada quando aplicável |
| `no_tracked_secrets` | Reprova nomes suspeitos versionados como segredos |

## Fluxo para adicionar componente

1. Criar `engineering/maturity/profiles/<id>.yaml`.
2. Declarar `evaluation_mode: shadow`.
3. Reutilizar suites comuns quando fizer sentido.
4. Criar `engineering/maturity/checks/<id>/pre-alpha-checks.yaml`.
5. Declarar scripts delegados no perfil, não no avaliador.
6. Executar `scripts/sge maturity publish` com `--component` e `--component-root`.
7. Confirmar `.run/maturity/components.json` e o Centro de Engenharia.
8. Registrar ADR quando o componente ganhar autoridade `governed`.

## Governança do módulo

O módulo de maturidade é parte do plano de controle do SGE. Mudanças nele podem
alterar a autoridade de promoção do ecossistema, portanto seguem regras
próprias.

Exigem registro arquitetural ou decisão equivalente:

- mudar `evaluation_mode`, `governance_authority` ou `promotion_enabled`;
- adicionar check obrigatório em estágio já usado para promoção;
- remover check obrigatório;
- alterar severidade de check;
- alterar semântica de tipo de check no avaliador;
- aceitar divergência entre `legacy` e `declarative`;
- retirar compatibilidade com `legacy`;
- mudar schema versionado em `contracts/engineering/` ou `contracts/maturity/`.

Critérios mínimos para novo check obrigatório:

1. possuir descrição orientada a evidência, não a implementação interna;
2. ter resultado reproduzível em ambiente limpo;
3. declarar artefato, script ou padrão verificável;
4. evitar dependência de caminho local privado;
5. definir se a falha bloqueia promoção ou apenas gera advertência;
6. estar coberto por validação contratual.

Componentes novos entram em `shadow` por padrão. A passagem para `governed`
deve declarar escopo bloqueante, responsável operacional e rollback.

## Códigos de saída

| Código | Significado |
|---|---|
| `0` | Avaliação válida e promoção permitida |
| `1` | Gate reprovado |
| `2` | Uso inválido do CLI |
| `3` | Contrato inválido |
| `4` | Erro de execução |
| `5` | Divergência entre engines |
| `6` | Falha de publicação |

## Referências

- [Centro de Engenharia](../../docs/architecture/MATURITY_DASHBOARD.md)
- [Arquitetura SGR](../../docs/architecture/sgr/)
- [Engines de verificação e modos de governança](../../docs/architecture/sgr/verification-engines-and-governance-modes.md)
- [Contrato de status de maturidade](../../contracts/maturity/1.0.0/README.md)
