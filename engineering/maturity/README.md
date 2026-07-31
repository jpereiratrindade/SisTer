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
| Publicador | `scripts/maturity/run-and-publish.sh` | Executa o gate, valida JSON, atualiza histórico e índice de componentes |
| Contratos | `contracts/engineering/` e `contracts/maturity/` | Definem formatos de entrada e saída |

`scripts/verify-sister-maturity.sh` continua como compatibilidade do Core
durante a transição, mas o destino arquitetural é o avaliador declarativo em
`scripts/maturity/evaluator.py`.

## Uso rápido

Avaliar e publicar o estágio inferido de `.sister/status.yml`:

```bash
./scripts/maturity/run-and-publish.sh
```

Avaliar e publicar um estágio específico do Core:

```bash
./scripts/maturity/run-and-publish.sh pre-alpha
./scripts/maturity/run-and-publish.sh alpha
```

Avaliar um componente federado em modo `shadow`:

```bash
./scripts/maturity/run-and-publish.sh pre-alpha \
  --component sister-clima \
  --component-root /caminho/para/sister-clima
```

Executar diretamente o motor declarativo, sem publicar histórico:

```bash
python3 scripts/maturity/evaluator.py \
  --repo "$PWD" \
  --component-root "$PWD" \
  --profile engineering/maturity/profiles/sister-core.yaml \
  --stage pre-alpha
```

Validar uma atestação JSON:

```bash
python3 scripts/maturity/validate-status.py .run/maturity/latest.json
```

## Arquivos produzidos

O publicador escreve em `.run/maturity/`, que não é versionado:

- `.run/maturity/latest.json`: última atestação publicada para consumo da UI;
- `.run/maturity/components.json`: índice federado dos componentes avaliados;
- `.run/maturity/components/<id>/latest.json`: última atestação do componente;
- `.run/maturity/components/<id>/history/*.json`: histórico do componente;
- `.run/maturity/components/<id>/history/index.json`: índice do histórico.

Relatórios Markdown tradicionais do Core continuam em `build/maturity/`.

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
6. Executar `scripts/maturity/run-and-publish.sh` com `--component` e `--component-root`.
7. Confirmar `.run/maturity/components.json` e o Centro de Engenharia.
8. Registrar ADR quando o componente ganhar autoridade `governed`.

## Referências

- [Centro de Engenharia](../../docs/architecture/MATURITY_DASHBOARD.md)
- [Arquitetura SGR](../../docs/architecture/sgr/)
- [Engines de verificação e modos de governança](../../docs/architecture/sgr/verification-engines-and-governance-modes.md)
- [Contrato de status de maturidade](../../contracts/maturity/1.0.0/README.md)
