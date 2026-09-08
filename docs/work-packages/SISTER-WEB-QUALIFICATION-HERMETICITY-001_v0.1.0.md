---
document_id: SISTER-WEB-QUALIFICATION-HERMETICITY-001
title: "SisTer Web — qualificação hermética dos testes de superfície"
version: "0.1.0"
status: "READY_FOR_EXECUTION"
date: "2026-09-08"
language: "pt-BR"
document_type: "corrective-execution-plan"
versioning: "semver"
indexable: true
executor: "Codex"
execution_authority: "FULL_DELIVERY_WITHIN_SCOPE"
workspace_root: "/run/media/jpereiratrindade/labeco10T/dev/cpp"
repositories:
  writable:
    - "SisTer"
    - "sister-infra"
  read_only:
    - "sister-atmos"
parent_plan: "SISTER-WEB-UX-001_v0.2.0"
previous_closure: "SISTER-WEB-UX-001-CLOSE-ATMOS_v0.1.0"
purpose: >-
  Restaurar a qualificação hermética do componente SisTer sem perder a prova
  genérica de propagação de superfícies nem o witness real Atmos → Infra → SisTer.
context: >-
  O lifecycle LAB falhou fechado durante QUALIFY porque um teste CTest do SisTer
  depende de repositórios irmãos que não existem na árvore temporária isolada
  criada por sister-component qualify. A correção é de fronteira e ownership de
  testes; não é uma nova implementação de produto.
baseline_observed:
  SisTer:
    branch: "main"
    head: "4dca10d"
  sister-infra:
    branch: "main"
    head: "59554a3"
  sister-atmos:
    branch: "main"
    head: "5bfd23c"
trigger:
  command: "./bin/sister-infra lifecycle run --target lab"
  result: "FAIL-CLOSED at QUALIFY"
  failed_test: "workspace_surface_propagation_tests"
  ctest_index: 33
index:
  domains:
    - web
    - qualification
    - testing
    - lifecycle
    - workspace
    - infrastructure
  keywords:
    - hermetic qualification
    - sister-component
    - CTest
    - workspace
    - interaction surface
    - cross-repository witness
    - fail-closed
    - test ownership
review:
  passes: 3
  focuses:
    - "causa raiz e fronteira de autoridade entre SisTer e sister-infra"
    - "gates mínimos, executabilidade e preservação do witness Atmos"
    - "ausência de impacto runtime, CPU/memória/I/O e condição de parada"
---

# 1. Missão

Corrigir **somente a fronteira de testes** que tornou a qualificação do SisTer
dependente de checkouts irmãos.

```text
qualificação SisTer
  deve depender apenas do clone isolado do SisTer

integração multi-repo
  pode depender de SisTer + sister-infra + sister-atmos
  mas não pode ser pré-condição da qualificação do componente
```

# 2. Causa raiz a confirmar

No estado observado:

- `tests/workspace_surface_propagation_test.py` procura `sister-infra` e
  `sister-atmos` via diretório pai do checkout SisTer;
- o teste está registrado no CTest padrão;
- `sister-component qualify` clona somente o componente em uma árvore temporária
  isolada e executa o CTest desse clone;
- portanto o teste externo falha durante `QUALIFY`, antes de qualquer mutação LAB.

**Não alterar `sister-component qualify` para clonar repositórios irmãos.**

# 3. Invariantes

1. Qualificação de componente é hermética em relação a repositórios irmãos.
2. SisTer testa localmente `SURFACE → workspace`.
3. Infra testa localmente `interaction_surface → public_url → SURFACE`.
4. O witness real `Atmos → Infra → SisTer` continua existindo, mas é integração
   multi-repositório explícita.
5. Nenhum hardcode por participante pode ser introduzido.
6. Nenhuma mudança de produto/runtime é desejada nesta missão.
7. O fail-closed do lifecycle deve ser preservado.

# 4. Escopo autorizado

## SisTer — escrita

Pode alterar somente o necessário em:

- `tests/workspace_surface_propagation_test.py` e/ou testes sucessores;
- `tests/CMakeLists.txt`;
- documentação diretamente afetada.

## sister-infra — escrita

Pode alterar somente testes se faltar cobertura própria da propagação genérica:

```text
descriptor interaction_surface
  → deployment resolve
  → resolved public_url
  → ecosystem projection SURFACE
```

Se cobertura equivalente já existir, **reutilizar e não duplicar**.

## sister-atmos — somente leitura

Serve apenas como witness real. Nenhuma alteração esperada.

# 5. Execução

## QH-01 — separar ownership dos testes

No SisTer, manter no CTest padrão uma prova determinística e autocontida de:

```text
fixture local de projection.tsv com SURFACE
  → sisterd
  → GET /api/v1/workspace
  → surfaces corretas e sem detalhes operacionais
```

Essa prova **não pode**:

- executar binários do `sister-infra`;
- ler `sister-atmos`;
- resolver caminhos de repositórios irmãos.

No Infra, confirmar ou criar a prova genérica neutra `alpha/beta/gamma` para a
parte que pertence ao Infra.

## QH-02 — preservar witness multi-repo

Preservar a prova real `Atmos → Infra → SisTer` como teste/witness de integração
explícito.

Ela deve receber caminhos de repositórios de forma explícita ou detectar sua
indisponibilidade de modo declarado. Não pode ser requisito para o CTest usado
por `sister-component qualify`.

Se registrada em uma suíte padrão onde dependências externas são opcionais,
usar a semântica de skip já adotada pelo projeto; não mascarar erro quando o
witness for invocado explicitamente com dependências válidas.

## QH-03 — provar qualificação real

Antes de qualquer lifecycle LAB, provar explicitamente a mesma fronteira:

```bash
cd /run/media/jpereiratrindade/labeco10T/dev/cpp/sister-infra

./bin/sister-component qualify \
  /run/media/jpereiratrindade/labeco10T/dev/cpp/SisTer \
  --contracts-root \
  /run/media/jpereiratrindade/labeco10T/dev/cpp/SisTer/contracts
```

Resultado obrigatório: `status PASS` e `tests.status PASS`.

# 6. Gates

A missão somente fecha se todos passarem:

### G1 — SisTer isolado

- build passa;
- CTest padrão passa, admitindo apenas skips já previstos por dependência
  externa legítima;
- nenhum teste obrigatório procura `../sister-infra` ou `../sister-atmos`.

### G2 — Qualificação

`./bin/sister-component qualify ...` passa contra o SisTer commitado.

### G3 — Infra

A propagação genérica neutra continua comprovada:

```text
path → public_url → SURFACE
```

sem decisão por identidade.

### G4 — witness real

No workspace multi-repo, Atmos continua chegando ao workspace por:

```text
sister-atmos → sister-infra → SisTer
```

### G5 — higiene

Nos repositórios alterados:

```bash
git diff --check
git status -sb
git log -5 --oneline --decorate
```

# 7. CPU / memória / I/O

Esta é uma correção de teste. Não autoriza:

- daemon, thread ou tarefa adicional;
- polling;
- health probe novo;
- cache novo;
- mudança de estratégia de snapshots;
- expansão de payload runtime.

Se qualquer código de produto precisar mudar, parar e demonstrar o defeito
independente que o torna necessário.

# 8. Proibido

- ensinar `sister-component qualify` a clonar dependências arbitrárias;
- remover ou enfraquecer o witness Atmos;
- transformar o witness real em fixture fictícia;
- hardcodar `Atmos`, `Nexo`, `URT`, `Praxis` ou `SisTer` para decidir lógica;
- executar `lifecycle run`, LAB apply ou production apply;
- fazer push;
- alterar contratos ou runtime sem defeito independente comprovado.

# 9. Commits

Criar somente commits correspondentes a alterações reais.

Preferência semântica:

```text
SisTer:
  test(workspace): keep component qualification hermetic

sister-infra, somente se necessário:
  test(projection): own generic surface propagation regression
```

# 10. Condição de parada

Parar antes de inventar solução se:

- a falha persistir sem depender de repositório irmão;
- surgir defeito de produto independente desta fronteira de teste;
- corrigir exigir alterar outro repositório ou contrato não autorizado;
- a prova real Atmos deixar de passar por motivo não relacionado ao split.

# 11. Witness final do Codex

Entregar de forma curta:

1. causa raiz confirmada;
2. ownership dos testes depois da correção;
3. arquivos e commits alterados;
4. CTest SisTer;
5. `sister-component qualify` PASS;
6. regressão genérica do Infra PASS;
7. witness Atmos multi-repo PASS;
8. `git diff --check` e `git status -sb`;
9. confirmação de que **nenhuma mutação LAB/PROD e nenhum push** ocorreu.

# 12. Definition of Done

```text
SisTer pode ser qualificado em isolamento
        +
Infra prova genericamente sua própria transformação
        +
witness Atmos continua provando integração multi-repo
        =
QUALIFICATION_HERMETICITY_RESTORED
```

Depois disso, a operação volta ao operador. O próximo passo será repetir
separadamente:

```bash
./bin/sister-infra lifecycle run --target lab
```

## Execução explícita do witness multi-repositório

O CTest padrão mantém `workspace_surface_propagation_tests` autocontido.
O Infra mantém a regressão em `tests/deployment_resolver_test.py`.
O witness real está fora do CTest de qualificação e exige dependências explícitas;
ausência de arquivos ou falha de integração resulta em erro, nunca sucesso/skip.

```bash
python3 SisTer/tests/workspace_atmos_integration_witness.py \
  --sister-root "$PWD/SisTer" \
  --infra-root "$PWD/sister-infra" \
  --atmos-root "$PWD/sister-atmos" \
  --sisterd "$PWD/SisTer/build/apps/sisterd/sisterd"
```

A composição workstation vigente do Infra também precisa ter seus participantes
locais disponíveis, conforme os caminhos declarados nela.
