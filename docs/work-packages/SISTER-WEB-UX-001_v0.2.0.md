---
document_id: SISTER-WEB-UX-001
title: "SisTer Web — projeções de usuário, ecossistema e engenharia"
version: "0.2.0"
status: "READY_FOR_EXECUTION"
date: "2026-09-04"
language: "pt-BR"
document_type: "implementation-plan"
versioning: "semver"
indexable: true
executor: "Codex"
execution_authority: "FULL_DELIVERY_WITHIN_SCOPE"
primary_repository: "SisTer"
conditional_repositories:
  - "sister-infra — somente para propagação genérica de binding/public_url"
  - "repositórios participantes — somente para declarar semântica que lhes pertence"
baseline_snapshot:
  source: "SisTer(20260904-093908).zip"
  observed_head: "7e00ca270dd2eed0b7fb532dddf143365a87248d"
  observed_commit: "7e00ca2 feat(ecosystem): adopt sister-atmos as a SisTer component"
  observed_branch_state: "main ahead 1 of origin/main"
purpose: >-
  Corrigir a Home autenticada e materializar a separação entre workspace do
  usuário, projeção semântica do ecossistema e observabilidade de engenharia,
  implementando somente fatos sustentados por fontes autoritativas vigentes.
context: >-
  O plano v0.1.0 separou Home de operação. Esta revisão incorpora a terceira
  projeção necessária — Ecossistema — para impedir que o SisTer Web termine como
  mero lançador de aplicações e para preservar relações, autoridade, evidência,
  proveniência e contexto como destino arquitetural.
supersedes:
  - "SISTER-WEB-UX-001_v0.1.0"
architecture_reference:
  - "docs/architecture/SISTER-WEB-RELATIONAL-SURFACE-001_v0.1.0.md"
related_documents:
  - "docs/architecture/SISTER_PARTICIPATION_ENGINEERING.md"
  - "docs/governance/ARTIFACT_STATUS.md"
  - "contracts/compatibility/SUBSYSTEM_1.0.0_TO_ARC01_DRAFTS.md"
index:
  domains: [web, ecosystem, workspace, semantic-projection, engineering, authorization, performance]
  keywords: [Home, Ecossistema, Engenharia, capability, interaction-surface, evidence, provenance, lazy-loading, CPU, memory, fail-closed]
review:
  passes: 3
  focuses:
    - "escopo, autoridade e ausência de segunda fonte de verdade"
    - "executabilidade, gates, testes e condição de parada"
    - "segurança, CPU/memória e compatibilidade evolutiva"
---

# 1. Missão

Executar uma reforma completa, porém incremental, da superfície Web:

```text
MEU AMBIENTE
→ o que o ator pode usar agora

ECOSSISTEMA
→ quem participa, com quais capacidades e autoridades; relações/evidências
  somente quando autoritativas

ENGENHARIA
→ o que está implantado, publicado e saudável
```

A entrega deve ficar **pronta para uso e pronta para evoluir**, sem inventar
semântica para preencher lacunas atuais.

# 2. Invariantes

1. Web é projeção derivada; não é fonte de verdade de participante/domínio.
2. Componente implantado não gera card automaticamente.
3. Capability não implica superfície navegável.
4. Runtime/health não implica governança, autorização ou aplicabilidade.
5. Relação técnica não implica `Relation` governada.
6. Nenhuma regra de visibilidade depende de IDs conhecidos.
7. Autorização é server-side; frontend apenas adapta apresentação.
8. Contratos DRAFT não ganham autoridade operacional para servir à UI.
9. Ausência de evidência produz ausência/estado explícito, nunca simulação.
10. A mudança deve reduzir recomputação e tráfego desnecessário.

# 3. Baseline factual a preservar/corrigir

No snapshot observado:

- `scripts/app/serve.sh` deriva `PARTICIPANT` diretamente de `.components[]`;
- `/api/ecosystem` e `/api/systems` parseiam a mesma projeção e executam health
  separadamente em cada requisição;
- `web/app.js` usa a projeção operacional como conteúdo principal da Home;
- `/engineering/` existe, mas sua rota estática ainda precisa de gate equivalente
  às APIs administrativas;
- `subsystem.manifest.read` é concedida a `researcher/project_lead` e hoje
  sustenta acesso a `/api/ecosystem`/`/api/systems`;
- `sister.participant/2.0.0`, `sister.capability-invocation/1.0.0` e
  `sister.relation/1.0.0` são DRAFT / NOT RUNTIME-NORMATIVE.

Não resetar o commit local observado para coincidir com `origin/main`.

# 4. Resultado final desta missão

```text
SisTer Web
├── Público
│   └── proposição institucional factual
├── Meu Ambiente
│   └── superfícies/ações realmente utilizáveis pelo ator
├── Ecossistema
│   └── fatos semânticos autorizados; sem relações inventadas
└── Engenharia
    └── projeção operacional completa
```

Se ainda não houver fonte autoritativa para uma categoria semântica, a página do
Ecossistema deve dizer isso por estado vazio factual.

# 5. Execução

## WEB-UX-00 — arqueologia curta e mapa de autoridade

Antes de editar:

```bash
git status -sb
git log -5 --oneline --decorate
git branch -vv
git remote -v
```

Identificar, sem alterar autoridade:

- fonte normativa atual de identidade/capabilities dos participantes;
- origem de `public_url`/binding resolvido;
- autoridade de identidade e capabilities do ator;
- consumidores atuais de `/api/ecosystem` e `/api/systems`;
- dados semânticos que são hoje fatos vigentes versus drafts/candidatos.

Produzir o menor mapa necessário e seguir para código. Não transformar a
arqueologia em nova fase documental.

## WEB-UX-01 — separar projeção operacional de workspace

Preservar `/api/ecosystem` como visão operacional de Engenharia.

Criar uma projeção pequena e versionada para a Home, preferencialmente:

```text
GET /api/v1/workspace
schema: sister.workspace-view/1.0.0
```

Campos mínimos de uma superfície finalística:

```text
surface_id
participant_id
label
purpose
public_url
availability
```

Somente quando já autoritativo:

```text
capability_ids
context_ref
reason/applicability summary
```

Nunca incluir no workspace:

```text
runtime.listen
runtime.port
probe.health_path
host interno
detalhes de deployment
```

A composição deve respeitar:

```text
participante → declara semântica própria
Infra         → resolve binding/public_url do ambiente
sisterd       → projeta para o ator autorizado
frontend      → renderiza
```

Se faltar declaração autoritativa, omitir a superfície. Não criar registry Web,
whitelist nem URL sintetizada. Se a declaração pertencer a outro repositório e ele
estiver disponível, corrigi-la no proprietário em commit separado; caso contrário,
seguir fail-closed e registrar a lacuna.

## WEB-UX-02 — materializar a projeção Ecossistema

Criar visão separada no frontend e uma projeção semântica compacta somente para
fatos sustentados por autoridade vigente. Preferir endpoint versionado, por exemplo
`GET /api/v1/ecosystem/semantic`, com status de contrato coerente com a maturidade
real da projeção.

A primeira entrega deve conseguir representar, quando disponíveis:

```text
participant_id / label
capabilities
papéis/authority scopes
estado semântico declarado
proveniência resumida
```

Relações, contexto e evidências entram **somente** quando houver fonte
operacionalmente legítima para elas.

Regras obrigatórias:

- não consumir `sister.relation/1.0.0` DRAFT como relação ativa;
- não promover drafts ARC-01;
- não desenhar Nexo→Praxis por conhecimento informal;
- não derivar relação de gateway, endpoint ou presença conjunta no deployment;
- estado vazio explícito é resultado válido.

Interface inicial: lista/tabela semântica acessível. Não criar grafo nesta
missão, salvo se a arqueologia provar relações autoritativas já vigentes e a
visualização puder ser totalmente derivada delas.

## WEB-UX-03 — reconstruir Meu Ambiente

Fluxo inicial obrigatório:

```text
1. GET /api/me
2. 401 → render público e parar
3. autenticado → GET /api/v1/workspace
4. demais visões → lazy-load ao abrir
```

Home autenticada:

```text
Meu Ambiente
[contexto atual, somente se factual]

Recursos disponíveis
  nome/finalidade
  disponibilidade simples
  ação
```

Remover da Home:

- contadores Participantes/Operacionais/Publicados/Deployment;
- cards de runtime;
- portas/probes/gateway;
- canvas “Leitura territorial” sintético;
- “Qualidade da rede” baseada apenas em operação;
- qualquer score decorativo.

SisTer e Praxis deixam de aparecer na Home **por semântica**, não por exceção de
nome. Nexo/URT/Atmos/futuros participantes seguem a mesma regra genérica.

## WEB-UX-04 — consolidar Engenharia

Mover/reutilizar a projeção operacional completa em `/engineering/`:

```text
componentes
composition/deployment
bindings
probes/health
gateway/publicação
diagnóstico operacional
```

Não duplicar parser, normalização ou health probe.

Proteger `/engineering`, `/engineering/` e seus recursos funcionais por
autorização server-side compatível com a capability de Engenharia escolhida.
Esconder link/DOM não conta como proteção.

## WEB-UX-05 — evidência e proveniência por expansão progressiva

Nesta missão, implementar somente quando a fonte atual já fornecer referências
confiáveis.

Padrão de UX desejado:

```text
resultado/resumo
  → Ver fundamento
      → evidência
      → proveniência
      → autoridade
      → tempo/contexto
```

Não copiar documentos completos nem criar banco de evidências Web.

Se a cadeia ainda não existir, não inventar placeholder que pareça evidência
real. Registrar a lacuna apenas no relatório final da missão.

## WEB-UX-06 — autorização e menor privilégio

Criar/reutilizar capabilities distintas para funções distintas quando o desenho
atual exigir:

```text
workspace de usuário
projeção semântica do ecossistema
observabilidade de engenharia
```

Os nomes finais pertencem ao vocabulário existente e devem ser escolhidos após a
arqueologia; não multiplicar capabilities sem necessidade.

Reavaliar `subsystem.manifest.read` em perfis comuns. Não mantê-la somente para
sustentar uma Home operacional.

O participante continua responsável pela autorização final do recurso que lhe
pertence.

# 6. CPU/memória — gate obrigatório

A entrega deve ser mais barata que a baseline no caminho comum.

## Frontend

```text
Público        → /api/me e parar
Meu Ambiente   → /api/me + workspace
Ecossistema    → lazy-load sem health por participante
Engenharia     → health/projeção operacional sob demanda
Detalhes       → evidência/proveniência sob demanda
```

Proibido:

- polling periódico novo;
- carregar APIs que a visão atual não usa;
- manter payload bruto + cópias normalizadas grandes sem justificativa;
- pré-carregar contratos/evidências/diagnósticos na Home.

## Backend

Eliminar a recomputação independente de parse + health entre consumidores
operacionais compatíveis.

Implementação deve possuir:

- observação operacional compartilhável por janela curta ou mecanismo bounded
  equivalente;
- invalidação determinística por revisão da fonte e/ou TTL curto;
- zero health para workspace e projeção semântica;
- concorrência limitada; nunca thread por participante/request sem limite;
- cache limitado em tamanho/tempo;
- nenhuma elevação de `SISTER_WORKERS` para esconder recomputação.

Em C++:

- preferir referências/`string_view` quando lifetime for claro;
- `reserve` quando cardinalidade for conhecida;
- `move` apenas onde evita cópia real;
- não persistir duplicatas do mesmo snapshot sem necessidade;
- evitar framework/cache pesado para resolver um snapshot pequeno.

## Witness de eficiência

Demonstrar por teste/instrumentação determinística, não por benchmark de máquina:

```text
público          → zero probes operacionais
Meu Ambiente     → zero probes operacionais
Ecossistema      → zero probes operacionais
Engenharia       → probes somente quando requisitada
/api/ecosystem + /api/systems → não duplicam observação dentro da janela definida
```

# 7. Testes obrigatórios

Usar fixtures neutras (`core`, `alpha`, `beta`, `gamma`, `delta`).

## T1 — separação das três projeções

```text
core  → componente operacional sem superfície finalística
alpha → capability + superfície de usuário
beta  → participante/capability sem superfície direta
gamma → componente apenas administrativo
```

Esperado:

```text
workspace comum  = [alpha]
ecosystem semantic = [alpha, beta] conforme autoridade vigente
engineering      = [core, alpha, beta, gamma]
```

## T2 — extensibilidade

Adicionar `delta` somente à fonte declarativa fixture. Nenhuma edição específica
do backend/frontend deve ser necessária.

## T3 — fail-closed de superfície

Participante online/publicado sem superfície finalística:

```text
workspace: ausente
engineering: presente
```

## T4 — relação não inventada

Fixture contém dois participantes tecnicamente publicados, mas nenhuma relação
autoritativa:

```text
Ecossistema: participantes presentes; relações = vazio/indisponível
```

## T5 — contrato de workspace

Resposta não contém detalhes internos de runtime/probe/deployment.

## T6 — segurança

Ator sem autoridade de Engenharia não obtém API operacional nem página funcional
de Engenharia. Validar API e rota estática.

## T7 — URL pública

Nenhum link de usuário é sintetizado de `listen/port`. Somente URL pública
resolvida por fonte competente.

## T8 — neutralidade

Nenhuma seleção/visibilidade em código de produção depende de:

```text
sister | nexo | praxis | urt | atmos
```

Nomes em docs/fixtures podem existir.

## T9 — lazy-loading

Teste/spy determinístico deve provar que abrir Home não solicita Ecossistema,
Engenharia, contratos, evidências ou diagnóstico.

## T10 — regressão

Executar, no mínimo, adaptando nomes ao harness real sem reduzir cobertura:

```bash
cmake --build build
ctest --test-dir build --output-on-failure
python3 tests/sisterd_ecosystem_api_test.py
python3 tests/engineering_operational_center_test.py
git diff --check
```

# 8. Arquivos prováveis, não prescritivos

```text
apps/sisterd/main.cpp
apps/sisterd/ecosystem/*
apps/sisterd/<workspace-or-semantic-projection>/*
web/index.html
web/app.js
web/styles.css
web/engineering/*
tests/*ecosystem*
tests/*workspace*
tests/*engineering*
contracts/*  # somente se autoridade e necessidade forem comprovadas
```

Codex pode reorganizar esses caminhos se encontrar uma fronteira melhor e os
gates permanecerem satisfeitos.

# 9. Restrições e condição de parada

Não:

```text
hardcodar IDs para visibilidade
criar catálogo manual no frontend
copiar projetos/atividades/contexto do Nexo
inventar Relation
usar DRAFT ARC-01 como runtime normativo
transformar capability em card automaticamente
usar READY/online como governança
criar score sem derivação
criar polling
adicionar cache/concorrência sem limite
expor host/porta interna a perfil comum
alterar DNS/TLS/produção
resetar Git para coincidir com origin
```

Parar e reportar antes de improvisar se:

1. a única solução exigir whitelist por participante;
2. faltar autoridade semântica indispensável e não houver fonte disponível;
3. a solução exigir promover contrato DRAFT;
4. runtime precisar ser usado como substituto de governança;
5. gate de autorização falhar;
6. eficiência depender de concorrência/cache sem limite;
7. a missão começar a reimplementar domínio de Nexo/URT/Atmos/Praxis.

# 10. Git e entrega

Commits devem representar unidades semânticas. Exemplo, ajustável ao código real:

```text
feat(web): add governed workspace projection
feat(web): add semantic ecosystem projection
refactor(web): isolate operational view in engineering
perf(sisterd): reuse bounded ecosystem observation
```

Antes de cada commit relevante:

```bash
git diff --check
git diff --stat
git diff
```

Antes da entrega:

```bash
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
git status -sb
git log -5 --oneline --decorate
```

Commit local após gates verdes é autorizado.

**Não fazer push, promoção LAB/PROD ou publicação remota sem autorização
separada.**

# 11. Definition of Done

Concluído somente quando:

1. Home comum representa somente superfícies/ações aplicáveis ao ator;
2. SisTer não aparece como card de si próprio sem regra especial de nome;
3. Praxis não aparece como aplicação geral por presença no deployment;
4. nenhum participante ganha card apenas por runtime/publicação;
5. existe visão Ecossistema separada de Home e Engenharia;
6. visão Ecossistema não apresenta relação não autoritativa como fato;
7. Home não contém topologia, portas, probes, deployment ou canvas sintético;
8. Engenharia concentra a projeção operacional e é protegida server-side;
9. workspace/semântica não executam probes de health;
10. público não dispara APIs protegidas desnecessárias;
11. lazy-loading está demonstrado por teste;
12. autorização permanece fail-closed;
13. não existe whitelist por `system_id`;
14. não existe segunda fonte de verdade Web para contexto/evidência;
15. contratos DRAFT permanecem sem autoridade operacional;
16. recomputação de parse/health operacional foi reduzida de forma bounded;
17. testes novos e regressivos passam;
18. `git diff --check` passa;
19. árvore final e commits são coesos e explicáveis.

# 12. Arco evolutivo preservado, fora do aceite imediato

A implementação atual deve deixar caminho aberto, sem simular essas etapas:

```text
P0 Meu Ambiente
P1 Ecossistema semântico
P2 contexto + evidência + proveniência
P3 composição governada
P4 reflexividade: evidência → avaliação → decisão → mudança
P5 inteligência relacional evidenciada
```

Cada etapa só avança quando a autoridade e a evidência vigentes a sustentarem.

> **A entrega deve estar pronta agora sem fingir que o ecossistema já materializa
> aquilo que ainda precisa provar.**
