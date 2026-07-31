# SisTer — Arquitetura do Processo de Engenharia, SGE-SisTer e Módulo de Maturidade

**Projeto:** SisTer — Sistema Inteligente e Resiliência de SSE  
**Tipo de documento:** Arquitetura, governança e estratégia de evolução  
**Status:** proposta para adoção arquitetural  
**Versão:** 1.0.0-draft  
**Implementação atual:** parcial  
**Extração para projeto independente:** não decidida  
**Próxima revisão:** após os pilotos Nexo e Clima  
**Escopo:** Processo de Engenharia do SisTer, SGE-SisTer, Módulo de Maturidade e Centro de Engenharia  
**Data de referência:** 31 de julho de 2026

---

## 1. Síntese executiva

O SisTer atingiu um estágio no qual a engenharia do próprio sistema passou a ser explicitamente governada por contratos, evidências, gates, aprovações e histórico de evolução.

Esse avanço revelou que o mecanismo criado não deve ser compreendido apenas como um controle de maturidade em estágios — Pré-Alfa, Alfa, Beta, Gama e Produção. O controle de maturidade é apenas uma parte de um processo mais amplo, que compreende:

- concepção;
- ontologia e domínio;
- arquitetura;
- ADRs;
- contratos;
- pacotes de trabalho;
- implementação;
- testes;
- governança;
- maturidade;
- promoção;
- operação.

A decisão arquitetural recomendada é:

> **Manter o Processo de Engenharia e o SGE-SisTer dentro do repositório SisTer como módulos explícitos, orientados por contratos e sem dependência irreversível do núcleo, permitindo extração futura para um projeto independente caso a reutilização entre subsistemas seja comprovada.**

A estratégia evita dois extremos:

1. extrair cedo demais um modelo ainda em consolidação;
2. permitir que o modelo amadureça de forma tão acoplada ao núcleo que sua reutilização futura se torne inviável.

O caminho adotado é:

> **modularizar primeiro; validar em múltiplos subsistemas; extrair depois, se houver evidência concreta.**

---

## 2. Contexto e motivação

O desenvolvimento do SisTer começou orientado principalmente por funcionalidades e integrações concretas. A incorporação de novos subsistemas, especialmente Clima e Nexo, revelou limitações arquiteturais importantes:

- concentração de responsabilidades no `sisterd`;
- integrações específicas codificadas no núcleo;
- transporte HTTP e WebSocket artesanal;
- repasse provisório de credenciais;
- ausência inicial de contratos comuns;
- necessidade de autorização por capacidades;
- necessidade de evidências de conformidade;
- necessidade de critérios objetivos para promoção.

Como resposta, foram criados:

- plano de transição do protótipo para produção;
- roteiro Alfa–Beta–Gama;
- gates de maturidade;
- verificador automatizado;
- atestações;
- histórico;
- Centro de Engenharia;
- SGE-SisTer.

Esse conjunto não constitui apenas uma ferramenta de avaliação. Ele materializa uma forma de conceber, desenvolver, validar, governar e promover sistemas e subsistemas.

---

## 3. Decisão arquitetural

### 3.1 Decisão principal

O Processo de Engenharia do SisTer e o SGE-SisTer serão consolidados como módulos internos reutilizáveis no repositório SisTer.

Esses módulos devem:

- possuir contratos próprios;
- evitar dependências irreversíveis do núcleo;
- ser parametrizáveis;
- operar sobre perfis de componentes;
- admitir checks específicos;
- produzir evidências estruturadas;
- manter histórico por componente;
- ser validados inicialmente no núcleo, Nexo e Clima.

A extração para um projeto independente será avaliada somente após evidência de reutilização real.

### 3.2 Consequências positivas

- preserva velocidade de evolução;
- evita fragmentação prematura;
- mantém documentação, código e governança próximos;
- permite validar o modelo com casos reais;
- facilita migração incremental;
- reduz risco de desenhar um framework abstrato sem uso comprovado;
- prepara extração futura com fronteiras conhecidas.

### 3.3 Consequências negativas

- parte do código permanecerá temporariamente específica do SisTer;
- haverá coexistência entre estrutura antiga e nova;
- a modularização exigirá refatoração gradual;
- contratos internos precisarão evoluir com compatibilidade;
- a equipe deverá impedir novos acoplamentos durante a transição.

---

## 4. Modelo conceitual

A arquitetura passa a ser compreendida em quatro níveis.

## 4.1 Processo de Engenharia do SisTer

É o processo completo pelo qual um componente do ecossistema nasce, evolui e chega à operação.

```text
Concepção
    ↓
Ontologia e domínio
    ↓
Arquitetura
    ↓
ADRs
    ↓
Contratos
    ↓
Pacotes de trabalho
    ↓
Implementação
    ↓
Testes
    ↓
Governança
    ↓
Maturidade
    ↓
Promoção
    ↓
Operação
```

Pergunta respondida:

> Como um componente do ecossistema SisTer deve ser concebido, desenvolvido, validado e promovido?

## 4.2 SGE-SisTer

O SGE-SisTer é o sistema de governança da engenharia.

```text
SGE-SisTer
├── decisões
├── contratos
├── evidências
├── aprovações
├── gates
├── histórico
├── métricas
├── Centro de Engenharia
└── promoções
```

Pergunta respondida:

> Como demonstramos que o processo foi seguido e que as decisões são sustentadas por evidências verificáveis?

## 4.3 Módulo de Maturidade

O Módulo de Maturidade é uma parte do SGE-SisTer.

```text
Maturidade
├── Pré-Alfa
├── Alfa
├── Beta
├── Gama
└── Produção
```

Pergunta respondida:

> Em qual estágio o componente está e o que falta para avançar?

## 4.4 Centro de Engenharia

O Centro de Engenharia é a interface visível do SGE-SisTer.

Ele:

- apresenta resultados;
- mostra bloqueadores;
- exibe histórico;
- comunica projeções explicativas;
- não executa decisões;
- não recalcula gates;
- não substitui o verificador;
- não aprova promoções.

Regra:

> **O processo orienta; o SGE governa; o módulo de maturidade verifica; o Centro de Engenharia comunica.**

---

## 5. Relação entre os componentes

```text
Processo de Engenharia do SisTer
│
├── Concepção e domínio
├── Arquitetura e ADRs
├── Contratos
├── Pacotes de trabalho
├── Implementação e testes
├── Operação
└── SGE-SisTer
    ├── Módulo de Maturidade
    ├── Evidências e aprovações
    ├── Histórico e métricas
    ├── Centro de Engenharia
    └── Radar de Engenharia
```

O SGE-SisTer não substitui o Processo de Engenharia. Ele governa e verifica parte dele.

O Módulo de Maturidade mede os estágios, identifica bloqueadores, produz atestações e recomenda a promoção. A promoção é uma decisão governada pelo SGE-SisTer, sustentada pelas evidências e aprovações exigidas.

O Centro de Engenharia não é a fonte de verdade. Ele projeta o estado produzido pelos mecanismos governados.

---

## 6. Estrutura recomendada no repositório

A estrutura-alvo deve ser introduzida gradualmente:

```text
SisTer/
├── contracts/
│   └── engineering/
│       ├── process/
│       │   └── 1.0.0/
│       ├── maturity-model/
│       │   └── 1.0.0/
│       ├── maturity-profile/
│       │   └── 1.0.0/
│       └── maturity-check/
│           └── 1.0.0/
├── engineering/
│   ├── README.md
│   ├── process/
│   │   ├── lifecycle.md
│   │   ├── decision-flow.md
│   │   ├── models/
│   │   └── templates/
│   ├── governance/
│   │   ├── README.md
│   │   ├── approvals/
│   │   ├── evidence/
│   │   └── policies/
│   ├── maturity/
│   │   ├── README.md
│   │   ├── engine/
│   │   ├── models/
│   │   ├── profiles/
│   │   ├── checks/
│   │   └── templates/
│   └── conformance/
│       ├── subsystem/
│       ├── application/
│       └── service/
├── scripts/
│   ├── engineering/
│   ├── maturity/
│   └── ci/
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── governance/
│   ├── runbooks/
│   └── evidence/
└── web/
    └── engineering/
```

### 6.1 Princípio da estrutura

Os contratos normativos possuem fonte canônica em `contracts/engineering/`.

O diretório `engineering/` deve reunir:

- modelos instanciados;
- perfis;
- políticas;
- checks declarativos;
- templates;
- mecanismos reutilizáveis que conformam aos contratos canônicos.

Os diretórios `docs/`, `scripts/` e `web/` permanecem como pontos de integração operacional.

> **Regra de fonte de verdade:** `contracts/engineering/` contém os contratos normativos e versionados; `engineering/` contém suas instâncias, configurações, perfis, templates e implementações.

### 6.2 Migração gradual

Não mover toda a estrutura atual de uma única vez.

Ordem recomendada:

1. criar a fronteira;
2. mover modelos e schemas;
3. introduzir perfis;
4. parametrizar o verificador;
5. separar checks específicos;
6. pilotar em Nexo;
7. pilotar em Clima;
8. decidir sobre extração.

---

## 7. Arquitetura do Módulo de Maturidade

O verificador atual ainda possui conhecimento específico do repositório:

- caminhos fixos;
- nomes de migrations;
- scripts específicos;
- quantidade mínima de ADRs;
- Clima;
- Nexo;
- gateway;
- estrutura do `sisterd`.

Para se tornar módulo reutilizável, deve ser decomposto em:

```text
motor genérico
+
modelo de maturidade
+
perfil do componente
+
checks locais
```

## 7.1 Motor genérico

Diretório sugerido:

```text
engineering/maturity/engine/
```

Responsabilidades:

- carregar modelo;
- validar configuração;
- resolver dependências entre estágios;
- executar checks;
- agregar resultados;
- produzir atestação;
- publicar histórico;
- validar aprovações;
- calcular elegibilidade e recomendação de promoção;
- preservar compatibilidade;
- produzir saída estruturada.

O motor não deve conhecer:

- Clima;
- Nexo;
- nomes de migrations;
- caminhos internos do `sisterd`;
- quantidade fixa de ADRs;
- regras científicas dos subsistemas.

## 7.2 Modelo de maturidade

Exemplo:

```yaml
schema: sister.maturity-model/1.0.0
model_id: sister.standard-maturity
version: 1.0.0

stages:
  - id: pre-alpha
    label: Pré-Alfa

  - id: alpha
    label: Alfa
    depends_on:
      - pre-alpha

  - id: beta
    label: Beta
    depends_on:
      - alpha

  - id: gamma
    label: Gama
    depends_on:
      - beta

  - id: production
    label: Produção
    depends_on:
      - gamma
```

## 7.3 Perfil do componente

### Perfil do núcleo

```yaml
schema: sister.maturity-profile/1.0.0
component_id: sister-core
component_type: platform-core
maturity_model: sister.standard-maturity/1.0.0

checks:
  alpha:
    - contract-common
    - identity-sessions
    - capabilities
    - architecture-approval
    - security-approval
```

### Perfil do Clima

```yaml
schema: sister.maturity-profile/1.0.0
component_id: sister-clima
component_type:
  - subsystem-http
  - subsystem-websocket
maturity_model: sister.standard-maturity/1.0.0

checks:
  alpha:
    - manifest
    - health
    - readiness
    - domain-boundaries

  beta:
    - signed-identity
    - websocket-limits
    - provider-degradation
    - gateway-conformance
```

## 7.4 Checks locais

Exemplo:

```yaml
schema: sister.maturity-check/1.0.0
id: session-token-hash
type: command
command: scripts/ci/check-session-token-hash.sh
mandatory: true
stage: alpha
dimension: security
description: Verifica que sessões persistem somente o hash do token.
```

Tipos iniciais de check:

- `command`;
- `file`;
- `directory`;
- `regex-present`;
- `regex-absent`;
- `schema`;
- `approval`;
- `http`;
- `manual-evidence`.

---

## 8. Arquitetura do Processo de Engenharia

O Processo de Engenharia também deve ser contratável e reutilizável.

Exemplo:

```yaml
schema: sister.engineering-process/1.0.0
process_id: sister.subsystem-development
version: 1.0.0

phases:
  - id: conception
    outputs:
      - domain-purpose
      - boundaries

  - id: architecture
    outputs:
      - architecture-reference
      - adrs

  - id: contracts
    outputs:
      - manifest
      - api-contracts
      - capabilities

  - id: implementation
    outputs:
      - code
      - migrations
      - tests

  - id: governance
    outputs:
      - maturity-evidence
      - approvals

  - id: operation
    outputs:
      - runbooks
      - monitoring
      - rollback
```

O processo deve permitir:

- fases obrigatórias;
- fases opcionais;
- entregas mínimas;
- responsáveis;
- critérios de aceite;
- referências a contratos;
- relação com gates;
- histórico de evolução.

---

## 9. Gabarito para novos subsistemas

O Processo de Engenharia deve evoluir para um gabarito operacional.

Exemplo futuro:

```bash
sisterctl engineering init-subsystem sister-solos
```

Estrutura criada:

```text
sister-solos/
├── docs/
│   ├── conception/
│   ├── architecture/
│   ├── adr/
│   └── runbooks/
├── contracts/
├── tests/
├── evidence/
├── engineering.yml
└── maturity.yml
```

O gabarito deve:

- criar estrutura;
- registrar identidade do componente;
- selecionar perfis;
- referenciar modelo de maturidade;
- gerar templates;
- não gerar aprovações;
- não marcar gates como aprovados;
- não criar testes que retornem sucesso automaticamente.

---

## 10. Estratégia de implantação

## 10.1 Etapa 1 — declarar a fronteira

Criar:

```text
engineering/
├── process/
├── governance/
├── maturity/
└── README.md
```

Declaração recomendada no `README.md`:

> O diretório `engineering/` reúne o Processo de Engenharia do SisTer, o SGE-SisTer e seus módulos reutilizáveis. Toda implementação deve evitar dependências irreversíveis do núcleo da plataforma.

## 10.2 Etapa 2 — criar contratos e modelos

Criar os contratos canônicos e versionados:

```text
contracts/engineering/process/1.0.0/
contracts/engineering/maturity-model/1.0.0/
contracts/engineering/maturity-profile/1.0.0/
contracts/engineering/maturity-check/1.0.0/
```

Criar as instâncias, modelos e templates que conformam a esses contratos:

```text
engineering/process/models/
engineering/process/templates/
engineering/maturity/models/
engineering/maturity/profiles/
engineering/maturity/checks/
engineering/maturity/templates/
```

## 10.3 Etapa 3 — parametrizar o verificador

Evoluir de:

```bash
verify-sister-maturity.sh --stage alpha
```

para:

```bash
verify-sister-maturity.sh \
  --component sister-core \
  --profile engineering/maturity/profiles/sister-core.yml \
  --stage alpha
```

Compatibilidade temporária:

```bash
verify-sister-maturity.sh --stage alpha
```

deve equivaler ao perfil padrão `sister-core`.

## 10.4 Etapa 4 — piloto no Nexo

Objetivo:

```text
mesmo motor
+
perfil distinto
+
checks distintos
+
histórico separado
```

O Nexo é o primeiro piloto porque valida:

- HTTP;
- autorização;
- capacidades;
- contratos;
- governança;
- integração sem a complexidade inicial do WebSocket.

## 10.5 Etapa 5 — piloto no Clima

O Clima deve validar:

- WebSocket;
- provedores externos;
- degradação;
- conexões persistentes;
- limites de recursos;
- identidade interna;
- gateway.

## 10.6 Etapa 6 — decisão sobre extração

Após os dois pilotos, criar ADR específico:

```text
ADR — Permanência interna ou extração do Framework de Engenharia
```

A decisão deve ser baseada em:

- reutilização real;
- estabilidade dos contratos;
- independência do motor;
- necessidade de ciclo de release próprio;
- custo de manutenção;
- impacto nos subsistemas.

---

## 11. Critérios para extração futura

A extração para projeto independente somente deve ocorrer quando:

1. dois ou mais subsistemas usam o mesmo motor sem modificá-lo;
2. o modelo possui contratos estáveis e versionados;
3. o motor executa sem depender da estrutura interna do repositório SisTer;
4. existe necessidade de releases independentes;
5. a extração reduz, e não aumenta, o custo de coordenação;
6. há responsáveis pela manutenção do projeto;
7. os subsistemas conseguem atualizar a dependência de forma controlada;
8. há estratégia de compatibilidade e migração.

Estrutura futura possível:

```text
dev/cpp/
├── SisTer/
├── sister-nexo/
├── sister-clima/
└── sister-engineering/
```

Produtos possíveis:

- `sister-maturity`;
- `sister-engineering-cli`;
- schemas;
- perfis;
- biblioteca de checks;
- gerador de projetos;
- publicador de evidências;
- interface incorporável.

---

## 12. Responsabilidades

## 12.1 Processo de Engenharia

Responsável por:

- ciclo de vida;
- artefatos esperados;
- transições;
- papéis;
- critérios de aceite;
- relação entre fases.

## 12.2 SGE-SisTer

Responsável por:

- governança;
- decisões;
- aprovações;
- evidências;
- histórico;
- políticas;
- promoções.

## 12.3 Módulo de Maturidade

Responsável por:

- estágios;
- checks;
- gates;
- atestações;
- bloqueadores;
- avaliação de elegibilidade e recomendação de promoção.

## 12.4 Centro de Engenharia

Responsável por:

- visualização;
- comunicação;
- histórico;
- métricas;
- projeções explicativas.

## 12.5 Subsistemas

Responsáveis por:

- perfis próprios;
- checks locais;
- evidências;
- conformidade;
- aprovações;
- operação.

---

## 13. Governança de mudanças

Toda mudança no Processo de Engenharia ou no Módulo de Maturidade deve indicar:

- contrato afetado;
- versão anterior;
- versão nova;
- compatibilidade;
- perfis afetados;
- migração necessária;
- testes de regressão;
- ADR, quando houver mudança estrutural.

Mudanças incompatíveis exigem nova versão principal do contrato.

---

## 14. Riscos

| ID | Risco | Impacto | Tratamento |
|---|---|---:|---|
| E-01 | Extrair cedo demais | Alto | validar primeiro em Nexo e Clima |
| E-02 | Acoplamento irreversível ao núcleo | Alto | contratos, perfis e motor genérico |
| E-03 | Governança virar burocracia | Alto | checks mínimos, perfis contextuais e automação |
| E-04 | Perfis divergirem sem controle | Médio/Alto | schema, versionamento e conformidade |
| E-05 | Motor executar comandos arbitrários | Crítico | comandos versionados, allowlist e ambiente controlado |
| E-06 | Aprovações serem tratadas como automáticas | Crítico | evidência humana explícita |
| E-07 | Comparar componentes incomparáveis | Médio | dimensões comuns e perfis contextualizados |
| E-08 | Reorganização quebrar o fluxo atual | Alto | migração gradual e compatibilidade |
| E-09 | Histórico perder proveniência | Alto | commit, digest, schema e assinatura |
| E-10 | Centro de Engenharia virar autoridade | Alto | verificador permanece fonte de verdade |

---

## 15. Pacotes de trabalho recomendados

## WP-ENG-01 — Fronteira de engenharia

**Entrega:** criar `engineering/` e documentação de escopo.  
**Aceite:** fronteira declarada sem mover componentes operacionais críticos.

## WP-ENG-02 — Contratos do processo

**Entrega:** `sister.engineering-process/1.0.0`.  
**Aceite:** fases, artefatos e critérios validados por schema.

## WP-MAT-01 — Modelo de maturidade

**Entrega:** `sister.maturity-model/1.0.0`.  
**Aceite:** Pré-Alfa, Alfa, Beta, Gama e Produção declarados fora do motor.

## WP-MAT-02 — Perfis de componentes

**Entrega:** perfis de núcleo, HTTP, WebSocket e serviço de dados.  
**Aceite:** checks selecionados por perfil.

## WP-MAT-03 — Motor parametrizado

**Entrega:** suporte a `--component` e `--profile`.  
**Aceite:** perfil `sister-core` reproduz o resultado atual.

## WP-MAT-04 — Piloto Nexo

**Entrega:** perfil e histórico próprios.  
**Aceite:** Nexo avaliado sem alteração do motor.

## WP-MAT-05 — Piloto Clima

**Entrega:** perfil WebSocket e checks específicos.  
**Aceite:** Clima avaliado sem alteração do motor.

## WP-ENG-03 — Decisão de extração

**Entrega:** ADR pós-pilotos.  
**Aceite:** decisão sustentada por evidências comparativas.

---

## 16. Critérios de aceite da modularização

A modularização inicial estará concluída quando:

- [ ] existir fronteira `engineering/`;
- [ ] os contratos normativos possuírem fonte canônica em `contracts/engineering/`;
- [ ] o Processo de Engenharia possuir contrato versionado;
- [ ] o modelo de maturidade estiver fora do motor;
- [ ] existir perfil `sister-core`;
- [ ] o verificador aceitar `--component` e `--profile`;
- [ ] o comportamento legado permanecer compatível;
- [ ] checks locais puderem ser adicionados sem alterar o motor;
- [ ] o histórico for separado por componente;
- [ ] o Centro de Engenharia mostrar múltiplos componentes;
- [ ] Nexo passar como primeiro piloto;
- [ ] Clima passar como segundo piloto;
- [ ] houver ADR sobre extração futura.

---

## 17. Evolução prevista

### Versão interna 1.0

- processo formal;
- motor ainda parcialmente específico;
- perfil do núcleo;
- Centro de Engenharia;
- histórico.

### Versão interna 1.1

- modelo externo;
- perfis;
- checks declarativos;
- múltiplos componentes.

### Versão interna 1.2

- Nexo e Clima;
- métricas comparáveis;
- conformidade por perfil.

### Versão 2.0

- Radar de Engenharia;
- gargalos;
- regressões;
- tendências;
- recomendações fundamentadas.

### Projeto independente

Somente após critérios de extração satisfeitos.

---

## 18. Nomenclatura adotada

### Conjunto completo

> **Processo de Engenharia do SisTer**

### Sistema de governança

> **SGE-SisTer**

### Controle de estágios

> **Módulo de Maturidade do SGE-SisTer**

### Interface

> **Centro de Engenharia do SisTer**

### Projeto independente futuro

> **SisTer Engineering Framework**

---

## 19. Frase de decisão

> **O Processo de Engenharia e o SGE-SisTer serão inicialmente consolidados como módulos internos, orientados por contratos e sem dependência irreversível do núcleo, para posterior extração caso a reutilização entre subsistemas seja comprovada.**

---

## 20. Conclusão

O caminho proposto é arquiteturalmente coerente e proporcional ao estágio atual do SisTer.

A separação imediata em outro repositório seria prematura, pois os contratos, o motor e os perfis ainda precisam ser validados em múltiplos componentes. Ao mesmo tempo, manter o processo misturado ao núcleo comprometeria a reutilização futura.

A estratégia recomendada combina aprendizado e disciplina:

1. declarar a fronteira;
2. modularizar contratos e modelos;
3. parametrizar o motor;
4. validar em Nexo;
5. validar em Clima;
6. medir o custo de reutilização;
7. decidir sobre extração por ADR.

O Processo de Engenharia passa, assim, a ser um patrimônio metodológico do ecossistema SisTer, enquanto o SGE-SisTer permanece como o mecanismo de governança que transforma decisões, testes e aprovações em evidências verificáveis.

> **Modularizar agora preserva a velocidade; preparar a extração preserva o futuro.**
