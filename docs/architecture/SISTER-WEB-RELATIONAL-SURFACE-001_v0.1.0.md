---
document_id: SISTER-WEB-RELATIONAL-SURFACE-001
title: "SisTer Web — superfície relacional e projeções"
version: "0.1.0"
status: "ACCEPTED_ARCHITECTURE"
date: "2026-09-04"
language: "pt-BR"
document_type: "architecture-directive"
versioning: "semver"
indexable: true
repository: "SisTer"
owner: "Arquitetura SisTer"
purpose: >-
  Definir o papel constitutivo da interface Web do SisTer como superfície de
  acesso, inteligibilidade e transparência do ecossistema, sem transferir para
  a Web autoridade pertencente aos participantes ou aos seus domínios.
context: >-
  A interface autenticada atual mistura experiência do usuário, projeção
  semântica do ecossistema e observabilidade operacional. A correção precisa
  separar essas funções sem reduzir o SisTer a um portal de aplicações.
scope:
  - "sister-web"
  - "sisterd projections"
  - "authorization boundaries"
  - "semantic presentation"
  - "operational observability"
normative_intent: "project-architecture"
supersedes: null
implemented_by:
  - "SISTER-WEB-UX-001_v0.2.0"
related_documents:
  - "docs/architecture/SISTER_PARTICIPATION_ENGINEERING.md"
  - "docs/governance/ARTIFACT_STATUS.md"
  - "contracts/compatibility/SUBSYSTEM_1.0.0_TO_ARC01_DRAFTS.md"
index:
  domains: [web, architecture, ecosystem, participation, relations, authority, provenance, evidence, performance]
  keywords: [workspace, semantic-ecosystem, engineering, capability, interaction-surface, context-ref, evidence-ref, provenance, CPU, memory]
review:
  passes: 3
  focuses:
    - "coerência constitutiva e autoridade"
    - "separação entre semântica, runtime e experiência"
    - "segurança, CPU/memória e evolução incremental"
---

# 1. Regra constitutiva

A Web do SisTer **revela o ecossistema; não se torna autoridade sobre ele**.

Ela deve derivar projeções de fontes autoritativas e responder, conforme a
permissão do ator:

```text
O que posso fazer?
Em qual contexto?
Quem fornece a capacidade?
Qual relação a torna possível?
Quem mantém autoridade sobre cada afirmação?
Que evidência e proveniência sustentam o resultado?
Qual é seu estado e sua temporalidade?
```

A ausência de fonte autoritativa deve produzir ausência, estado desconhecido ou
indisponibilidade explícita — nunca inferência visual apresentada como fato.

# 2. Três projeções independentes

```text
MEU AMBIENTE
→ o que o ator pode utilizar agora

ECOSSISTEMA
→ participantes, capacidades, relações, autoridade, contexto e evidência

ENGENHARIA
→ deployment, bindings, gateway, probes, health e diagnóstico
```

Uma fonte pode alimentar mais de uma projeção, mas as projeções não são
intercambiáveis.

```text
runtime online      != capacidade aplicável
capacidade existente != superfície navegável
publicado             != autorizado
relação proposta      != relação aceita
resultado disponível  != resultado evidenciado
```

# 3. Unidade semântica da experiência

A unidade de apresentação não é necessariamente o sistema.

Distinguir:

```text
CAPABILITY
→ algo que um participante pode realizar

INTERACTION SURFACE
→ ponto finalístico que o usuário pode acessar diretamente

COMPOSED ACTION
→ ação oferecida pela composição governada de capacidades
```

Uma capability não gera card automaticamente. Um participante pode participar
sem possuir interface direta para o usuário.

Quando houver relação governada autoritativa, a apresentação deve privilegiar:

```text
CAPACIDADE
  dentro de RELAÇÃO
  situada em CONTEXTO
  sustentada por EVIDÊNCIA
```

# 4. Autoridade e fontes de verdade

A Web e o `sisterd` não devem criar uma segunda verdade para domínios externos.

Exemplo de fronteiras:

```text
participante → identidade, capability, autoridade e limites que lhe pertencem
Nexo         → contexto e decisões do domínio sob sua autoridade
Atmos        → afirmações climáticas sob sua autoridade
URT          → observações sob sua autoridade
Praxis       → avaliações metodológicas sob sua autoridade
SisTer       → composição, projeção e governança que efetivamente lhe pertençam
Infra        → binding e publicação do ambiente
```

Contexto externo deve entrar por referência autorizada, não por réplica local:

```text
context_ref:
  authority
  type
  id
  label
  revision/version  # quando a fonte oferecer
```

O mesmo princípio vale para evidência e proveniência: transportar referências e
resumos necessários; carregar detalhes sob demanda.

# 5. Relações: somente fatos governados

`sister.participant/2.0.0`, `sister.capability-invocation/1.0.0` e
`sister.relation/1.0.0` permanecem **DRAFT / NOT RUNTIME-NORMATIVE** enquanto a
autoridade vigente assim os classificar.

Portanto:

- não promover esses drafts para resolver a UI;
- não desenhar arestas Nexo↔Praxis por conhecimento informal;
- não converter integração técnica em relação aceita;
- separar claramente candidato/proposta de estado governado, quando candidatos
  forem mostrados por motivo legítimo.

Até existir relação autoritativa, uma visão sem grafo e com estado vazio factual
é mais correta que uma visualização inventada.

# 6. Evidência, proveniência e temporalidade

Resultados relevantes devem poder evoluir para uma explicação progressiva:

```text
resultado
→ fundamento
→ evidência
→ proveniência
→ participante/autoridade
→ contexto
→ tempo
```

A interface deve distinguir, quando a fonte autoritativa permitir:

```text
observado em
válido para
calculado em
baseado em
atualizado em
```

Disponibilidade operacional também não substitui estado epistêmico. A
arquitetura deve comportar sem colapsar conceitos como:

```text
ONLINE | OFFLINE | DEGRADED
STALE | NOT_OBSERVED | NO_EVIDENCE
NOT_APPLICABLE | NOT_AUTHORIZED | SUSPENDED
```

Não é obrigatório materializar todos esses estados na primeira entrega; é
obrigatório não projetar um contrato que torne impossível distingui-los depois.

# 7. Experiência por projeção

## 7.1 Meu Ambiente

Mostra somente ações/superfícies aplicáveis ao ator e ao contexto disponível.

Não mostra portas, probes, host interno, deployment ou topologia operacional.

## 7.2 Ecossistema

Mostra fatos semânticos autorizados: participantes, papéis, capabilities,
autoridades e, quando existirem de forma governada, relações, contexto,
evidência e proveniência.

A primeira representação deve ser lista/tabela semanticamente explícita. Grafos
são opcionais e somente derivados de relações autoritativas.

## 7.3 Engenharia

Mostra fatos operacionais: componentes implantados, bindings, gateway,
publicação, probes, health, diagnóstico e demais informações técnicas.

É superfície com autorização própria e proteção server-side.

# 8. Segurança e continuidade federada

Visibilidade da projeção semântica também é autorizada server-side.

O SisTer pode decidir se apresenta uma ação, mas a autorização final sobre o
recurso continua pertencendo ao participante competente.

A experiência deve evoluir para continuidade de identidade entre participantes
sem compartilhar senhas nem transformar sessão/cookie do SisTer em credencial
universal.

```text
federado != fragmentado
federado != autoridade central absoluta
```

# 9. CPU/memória como requisito arquitetural

A separação de projeções deve **reduzir trabalho por requisição**.

```text
PUBLIC
  identidade mínima; zero probes

MEU AMBIENTE
  identidade + workspace compacto

ECOSSISTEMA
  snapshot semântico compacto e lazy

DETALHE
  evidência/proveniência lazy

ENGENHARIA
  observação operacional sob demanda
```

Regras:

- não executar health para montar workspace ou visão semântica;
- não criar polling por padrão;
- não duplicar raw + normalizado sem justificativa;
- parsear/reutilizar fontes enquanto sua revisão não mudar;
- cache e concorrência sempre bounded e com invalidação determinística;
- preferir summaries + refs + paginação a payloads integrais;
- em C++, evitar cópias evitáveis e estruturas persistentes sem necessidade;
- não aumentar workers para mascarar recomputação redundante.

# 10. Gates constitutivos da interface

Usar a escada C0–C6 como critério de representação, não como badge decorativo:

| Gate | A Web só pode revelar como fato quando houver evidência para |
|---|---|
| C1 | identidade, capability, autoridade e estado do participante |
| C2 | relação governada real e evidências associadas |
| C3 | múltiplas relações descobríveis/reconstruíveis |
| C4 | resultado produzido por composição de capacidades |
| C5 | trajetória evidência → avaliação → decisão → mudança |
| C6 | capacidade emergente demonstrável da composição |

A UI não promove o ecossistema entre gates. Ela apenas revela o que a autoridade
e a evidência vigentes sustentam.

# 11. Antipadrões proibidos

```text
catálogo manual de sistemas no frontend
whitelist por system_id
card automático por presença no deployment
grafo inferido por nomes conhecidos
cópia local de contexto pertencente a outro domínio
online == autorizado
READY == governado
capability == interface
integração técnica == relação aceita
score ou maturidade sem derivação verificável
health repetido por tela
promoção de contrato DRAFT para atender a UX
```

# 12. Critério de sucesso

A arquitetura estará corretamente materializada quando um ator autorizado puder
compreender **o que pode fazer, quem participa, por qual capacidade, sob qual
autoridade, contexto e evidência**, enquanto a Web permanece uma projeção
derivada e a observabilidade operacional continua separada.

> **Meu Ambiente mostra o que posso fazer; Ecossistema explica como o SisTer se
> relaciona; Engenharia mostra como ele está operando.**
