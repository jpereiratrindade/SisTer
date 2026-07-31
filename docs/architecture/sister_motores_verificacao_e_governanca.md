# Motores de Verificação e Modos de Governança no Ecossistema SisTer

**Documento de referência arquitetural e operacional**  
**Versão:** 1.0  
**Data:** 31 de julho de 2026  
**Escopo:** SGR, SisTer-Core e componentes federados do ecossistema SisTer

---

## 1. Propósito

Este documento formaliza a distinção entre:

1. os **motores de verificação de maturidade** — `legacy`, `declarative` e `compare`; e
2. os **modos de governança dos componentes** — `shadow` e `governed`.

A separação é necessária porque esses conceitos atuam em camadas distintas:

- o **engine** determina **como** os critérios de maturidade são interpretados e executados;
- o **modo de governança** determina **que autoridade** o resultado de um componente possui sobre gates, promoções e decisões do ecossistema.

A síntese arquitetural é:

> **O engine determina como a maturidade é verificada; o modo de governança determina que autoridade o resultado possui sobre o ecossistema.**

Em termos operacionais:

> **`compare` protege a migração do verificador; `shadow` protege a evolução federada do ecossistema.**

---

## 2. Problema que esta separação resolve

Sem uma distinção explícita entre execução e governança, quatro erros se tornam prováveis:

1. interpretar `legacy` como oposto de `shadow`;
2. tratar uma falha técnica como bloqueio sistêmico automático;
3. promover componentes experimentais cedo demais;
4. manter motores antigos indefinidamente por ausência de critérios de retirada.

A arquitetura correta possui dois eixos independentes:

```text
EIXO A — EXECUÇÃO DO VERIFICADOR
├── legacy
├── declarative
└── compare

EIXO B — AUTORIDADE DE GOVERNANÇA
├── shadow
└── governed
```

Esses eixos podem ser combinados:

```text
engine: compare
governance_mode: shadow
```

Nesse caso:

- o componente é verificado pelos motores antigo e novo;
- os resultados são comparados;
- divergências são tratadas como problema da migração;
- uma reprovação do componente é registrada;
- a falha não bloqueia a promoção global.

Portanto, `legacy` e `shadow` não são alternativas concorrentes. Eles respondem a perguntas diferentes.

---

## 3. Modelo conceitual

### 3.1 Fluxo de verificação

```text
Perfil de maturidade
        │
        ▼
Engine selecionado
        │
        ├── legacy
        ├── declarative
        └── compare
        │
        ▼
Execução dos checks
        │
        ▼
Resultado técnico
PASS | FAIL | SKIP | ERROR
        │
        ▼
Aplicação da governança
        │
        ├── shadow   → registra, recomenda, não bloqueia
        └── governed → registra, recomenda e pode bloquear
```

### 3.2 Perguntas fundamentais

| Camada | Pergunta |
|---|---|
| Engine | Qual implementação executará e interpretará os critérios de maturidade? |
| Governança | Qual efeito o resultado terá sobre a promoção do ecossistema? |
| Maturidade | Em que estágio o componente se encontra? |
| Criticidade | A falha desse componente compromete quais capacidades? |
| Operação | Quem responde pela falha e qual procedimento deve ser acionado? |

---

## 4. Motores de verificação

## 4.1 `legacy`

### Definição

O modo `legacy` executa o mecanismo histórico de verificação, normalmente baseado em regras codificadas diretamente em scripts Bash.

Exemplo:

```bash
./verify-sister-maturity.sh --engine legacy
```

### Pergunta que responde

> Qual resultado o mecanismo anterior produz para este conjunto de critérios?

### Função arquitetural

Durante a transição, o `legacy` atua como referência histórica de comportamento. Ele permite:

- reproduzir resultados antigos;
- diagnosticar regressões;
- identificar ambiguidades;
- verificar compatibilidade;
- sustentar a validação cruzada do modo `compare`.

### Quando usar isoladamente

O `legacy` deve ser executado sozinho quando:

1. o `compare` indicar divergência;
2. houver suspeita de regressão no motor declarativo;
3. for necessário reproduzir um resultado histórico;
4. for preciso demonstrar uma limitação do comportamento antigo;
5. estiver sendo preparada sua retirada definitiva;
6. um incidente exigir a reconstrução da cadeia de decisão anterior.

### Quando não usar

O `legacy` não deve ser:

- o modo operacional padrão;
- a base para novos checks;
- usado para contornar divergências sem investigação;
- mantido como dependência permanente sem justificativa.

### Efeitos práticos no desenvolvimento

- mantém compatibilidade temporária;
- aumenta o custo de manutenção enquanto houver dois motores;
- permite diagnóstico de regressões;
- exige testes que comprovem equivalência semântica;
- funciona como proteção contra uma migração declarativa incompleta.

### Efeitos práticos no produto em produção

O `legacy`, por si só, não determina se uma versão será promovida. Seu efeito é indireto:

- pode confirmar que o novo verificador preserva o comportamento anterior;
- pode revelar que uma decisão de promoção foi produzida por uma divergência;
- pode sustentar auditorias e análises de incidentes;
- reduz o risco de uma mudança silenciosa na política de maturidade.

### Posição recomendada

> O `legacy` permanece como instrumento temporário de diagnóstico e compatibilidade, não como destino arquitetural.

---

## 4.2 `declarative`

### Definição

O modo `declarative` executa o novo motor orientado por perfis e contratos declarativos.

Exemplo:

```bash
./verify-sister-maturity.sh --engine declarative
```

Os critérios deixam de estar dispersos em lógica procedural e passam a ser definidos por artefatos como:

```text
maturity profile
├── gates
├── checks
├── comandos
├── pré-condições
├── severidades
├── evidências
└── efeitos esperados
```

### Pergunta que responde

> O motor orientado por declarações interpreta corretamente os contratos de maturidade?

### Função arquitetural

O `declarative` é a direção estrutural do SGR porque:

- separa política de execução;
- reduz acoplamento entre Core e componentes;
- permite que domínios federados declarem checks próprios;
- torna regras versionáveis e auditáveis;
- facilita evolução sem alterar o motor central;
- melhora reuso e consistência.

### Quando usar isoladamente

Use o `declarative` sozinho para:

- desenvolver novos checks;
- depurar perfis YAML;
- validar novas capacidades;
- testar regras inexistentes no motor antigo;
- avaliar desempenho;
- preparar a retirada do `legacy`;
- investigar o comportamento nativo do novo motor.

### Efeitos práticos no desenvolvimento

- novos critérios são desenvolvidos como configuração versionada;
- revisões de código passam a avaliar semântica, schema e evidências;
- componentes podem evoluir com maior autonomia;
- regras tornam-se mais fáceis de testar e documentar;
- o Core deixa de precisar conhecer detalhes internos de cada domínio.

### Efeitos práticos no produto em produção

- reduz risco de comportamento oculto em scripts;
- melhora rastreabilidade da decisão de promoção;
- facilita explicar por que um componente passou ou falhou;
- permite evolução controlada dos gates;
- amplia a capacidade de auditoria;
- favorece governança federada sem transformar o Core em um catálogo de exceções.

### Posição recomendada

> O `declarative` é o motor de destino, mas deve assumir autoridade plena somente após demonstrar equivalência, estabilidade e capacidade de diagnóstico.

---

## 4.3 `compare`

### Definição

O modo `compare` executa os motores `legacy` e `declarative` e compara seus resultados.

Exemplo:

```bash
./verify-sister-maturity.sh --engine compare
```

Fluxo simplificado:

```text
                 ┌── legacy ────────┐
perfil/checks ───┤                   ├── comparação semântica
                 └── declarative ───┘
```

### Pergunta que responde

> O motor declarativo preserva a semântica esperada do motor legado?

### Função arquitetural

O `compare` não é somente uma opção de execução. Ele é um mecanismo temporário de governança da migração.

Ele protege contra:

- perda silenciosa de checks;
- mudanças de interpretação;
- diferenças de severidade;
- tratamento inconsistente de códigos de saída;
- coleta desigual de evidências;
- promoções indevidas;
- confiança prematura no novo motor.

### O que uma divergência significa

Uma divergência não prova automaticamente que o `declarative` está errado. Ela pode revelar:

- defeito no motor novo;
- defeito já existente no legado;
- perfil ambíguo;
- normalização diferente;
- semântica incompleta;
- evidência coletada em formatos distintos;
- regra antiga que precisa ser deliberadamente superada.

### Procedimento obrigatório diante de divergência

```text
1. Registrar o caso e preservar as evidências.
2. Executar o modo legacy isoladamente.
3. Executar o modo declarative isoladamente.
4. Comparar checks individuais, códigos de saída e evidências.
5. Identificar qual semântica é correta.
6. Corrigir motor, perfil, normalização ou contrato.
7. Registrar a decisão.
8. Reexecutar o compare.
9. Encerrar somente após convergência ou divergência formalmente aceita.
```

### Efeitos práticos no desenvolvimento

- transforma a migração em processo verificável;
- impede aceitação baseada apenas em impressão;
- favorece testes de regressão;
- exige critérios explícitos para divergências intencionais;
- cria evidência para a futura remoção do legado.

### Efeitos práticos no produto em produção

- reduz o risco de o SGR mudar silenciosamente sua política;
- aumenta confiança em promoções;
- permite explicar diferenças entre versões;
- ajuda a separar falha do produto de falha do próprio verificador;
- sustenta auditorias e pós-incidentes.

### Posição recomendada

> Durante a transição, `compare` deve ser o modo padrão. Após a estabilização do motor declarativo e a retirada do legado, deixa de ser necessário.

---

## 5. Modos de governança

## 5.1 `shadow`

### Definição

Um componente em `shadow` participa da esteira, produz evidências e aparece no SGR, mas seu resultado não possui poder de veto sobre a promoção global.

Exemplo:

```yaml
governance_mode: shadow
```

### Pergunta que responde

> O resultado deste componente deve ser observado sem bloquear a promoção global?

### Características

Um componente `shadow`:

- é reconhecido pelo ecossistema;
- executa checks reais;
- produz PASS, FAIL, SKIP ou ERROR;
- aparece nos relatórios e painéis;
- acumula histórico;
- pode gerar alertas e recomendações;
- não bloqueia a promoção global.

### Significado correto

> `shadow` não significa ignorado; significa avaliado sem autoridade bloqueante.

### Quando usar

- piloto;
- pré-alfa;
- integração experimental;
- componente sem SLA;
- subsistema não crítico;
- dependência externa instável;
- domínio em processo de descoberta de critérios;
- componente útil, mas não estrutural para o Core.

### Efeitos práticos no desenvolvimento

- permite integrar cedo sem comprometer a esteira;
- acelera aprendizado;
- revela dependências e critérios reais;
- possibilita observação de falhas recorrentes;
- reduz pressão para “maquiar” checks a fim de evitar bloqueios;
- cria histórico para decisões futuras.

### Efeitos práticos no produto em produção

- uma falha fica visível, mas não interrompe capacidades não relacionadas;
- o produto pode operar com degradação conhecida;
- o SGR comunica risco sem transformar toda falha em indisponibilidade global;
- reduz o raio de impacto de componentes experimentais;
- permite evolução incremental e federada.

### Riscos

O uso inadequado de `shadow` pode:

- normalizar falhas persistentes;
- esconder ausência de responsável;
- manter componentes indefinidamente em estado experimental;
- criar falsa sensação de segurança se o painel não comunicar gravidade.

### Controles necessários

- responsável definido;
- histórico de execução;
- revisão periódica;
- critérios de permanência;
- registro de riscos;
- recomendação explícita;
- alerta para falhas críticas mesmo sem bloqueio.

---

## 5.2 `governed`

### Definição

Um componente em `governed` participa da esteira com autoridade para bloquear promoções dentro do escopo definido.

Exemplo:

```yaml
governance_mode: governed
```

### Pergunta que responde

> A saúde deste componente é condição necessária para promover o sistema ou uma capacidade específica?

### Características

Uma falha pode produzir:

```text
componente governed falha
        ↓
gate reprova
        ↓
promoção é bloqueada
```

### Significado arquitetural

Tornar um componente `governed` equivale a declarar:

> O sistema, ou a capacidade governada, não pode ser considerado apto quando este componente não estiver apto.

Isso é mais forte do que afirmar que o componente é estável. Implica dependência, criticidade e responsabilidade operacional.

### Quando usar

- componente estrutural;
- dependência necessária para a capacidade promovida;
- contrato estável e versionado;
- checks reprodutíveis;
- responsável operacional definido;
- impacto de falha conhecido;
- decisão formal da governança.

### Efeitos práticos no desenvolvimento

- falhas passam a bloquear merges, releases ou promoções;
- aumenta a exigência de estabilidade dos checks;
- falso positivo torna-se incidente de entrega;
- contratos e perfis exigem controle de mudança;
- simulações de falha e rollback tornam-se obrigatórias;
- responsabilidade operacional precisa estar clara.

### Efeitos práticos no produto em produção

- reduz a chance de promover uma versão incompatível;
- protege capacidades essenciais;
- aumenta confiança na coerência do produto;
- pode reduzir velocidade de entrega;
- amplia o impacto de checks instáveis;
- exige mecanismos de exceção, suspensão e recuperação.

### Riscos

- bloqueio global por falha irrelevante;
- acoplamento excessivo;
- paralisia da esteira;
- falsos negativos ou positivos com grande impacto;
- uso político do gate sem critério técnico.

### Controles necessários

- escopo claro;
- justificativa de criticidade;
- responsável e SLA;
- política de exceção;
- rollback;
- versionamento;
- observabilidade;
- revisão periódica.

---

## 6. Matriz de combinações

| Engine | Governança | Uso recomendado | Efeito sobre promoção |
|---|---|---|---|
| `compare` | `shadow` | Integração e migração seguras de componentes experimentais | Registra divergências e falhas, sem bloqueio global |
| `declarative` | `shadow` | Desenvolvimento de checks e pilotos com o novo motor | Observa sem bloquear |
| `legacy` | `shadow` | Diagnóstico histórico de componente não crítico | Observa sem bloquear |
| `compare` | `governed` | Componente crítico durante a migração do motor | Pode bloquear; divergência exige investigação |
| `declarative` | `governed` | Estado de destino após estabilização | Pode bloquear conforme o escopo |
| `legacy` | `governed` | Estado transitório ou contingencial | Pode bloquear, mas não é destino desejável |

---

## 7. Impactos no processo de desenvolvimento

## 7.1 Criação ou alteração de checks

Fluxo recomendado:

```text
1. Definir o objetivo do check.
2. Declarar entrada, comando, severidade e evidência.
3. Testar com --engine declarative.
4. Validar casos PASS, FAIL, SKIP e ERROR.
5. Executar com --engine compare.
6. Investigar divergências.
7. Submeter perfil e testes à revisão.
8. Registrar a decisão no histórico.
```

### Critérios mínimos de aceite

- check determinístico ou tolerâncias explicitadas;
- mensagem de erro compreensível;
- evidência preservada;
- código de saída normalizado;
- severidade justificada;
- impacto sobre gates conhecido;
- comportamento testado nos dois motores enquanto durar a transição.

---

## 7.2 Revisão de código e integração contínua

Uma revisão não deve avaliar apenas se “o teste passou”. Deve verificar:

- qual engine produziu o resultado;
- se houve divergência;
- se a evidência é suficiente;
- se o componente é `shadow` ou `governed`;
- qual gate foi afetado;
- se a falha é local ou sistêmica;
- se o perfil alterou autoridade de bloqueio;
- se a mudança exige registro de decisão.

### Regra de ouro

> Alterar `governance_mode` é uma mudança arquitetural, não uma simples edição de configuração.

---

## 7.3 Desenvolvimento federado

O modelo favorece autonomia porque:

- o Core fornece o mecanismo;
- cada componente declara seus critérios;
- o SGR agrega resultados;
- a governança define o efeito;
- componentes experimentais podem participar sem poder de veto.

Isso reduz o acoplamento entre equipes e permite evolução assimétrica:

```text
componente estável        → governed, se crítico
componente experimental   → shadow
motor em transição        → compare
motor estabilizado        → declarative
```

---

## 8. Impactos no produto e no processo em produção

O SisTer deve ser compreendido simultaneamente como:

1. **produto em execução**, formado por capacidades disponíveis aos usuários; e
2. **processo contínuo de produção**, formado por desenvolvimento, verificação, promoção, observação e aprendizado.

Os modos afetam os dois aspectos.

## 8.1 Impacto sobre o produto em execução

### Disponibilidade

- `shadow` permite manter disponíveis capacidades não relacionadas à falha;
- `governed` impede promover versões que comprometam capacidades essenciais.

### Degradação controlada

Um componente `shadow` pode falhar sem derrubar o conjunto, desde que:

- sua indisponibilidade seja comunicada;
- não haja corrupção de dados;
- o restante do produto continue coerente;
- o SGR registre a degradação.

### Coerência

O objetivo não é manter tudo sempre ativo, mas garantir que o sistema permaneça coerente enquanto se reconfigura diante de falhas.

Essa é uma expressão prática de resiliência:

> **O produto resiliente não oculta a perturbação; ele limita seus efeitos, preserva coerência e registra a reconfiguração.**

---

## 8.2 Impacto sobre o processo de produção

### Segurança da promoção

- `compare` protege contra alteração silenciosa do critério;
- `governed` protege contra promover componentes essenciais reprovados;
- `shadow` evita que componentes experimentais paralisem o processo.

### Velocidade de entrega

- `shadow` favorece experimentação;
- `governed` aumenta controle, mas pode reduzir velocidade;
- `compare` aumenta custo temporário, mas reduz risco de migração.

### Auditabilidade

Cada decisão deve permitir responder:

- qual perfil foi usado;
- qual engine executou;
- quais checks rodaram;
- quais evidências foram coletadas;
- qual modo de governança foi aplicado;
- por que a promoção foi permitida ou bloqueada;
- quem aprovou eventual exceção.

### Aprendizado operacional

O histórico permite:

- descobrir checks frágeis;
- identificar falhas recorrentes;
- medir estabilidade;
- decidir se um componente deve mudar de modo;
- comprovar quando o legado pode ser retirado.

---

## 9. Governança contextual e escopo de bloqueio

A evolução recomendada não deve se limitar a uma escolha global entre `shadow` e `governed`.

Um componente pode ser crítico para uma capacidade e irrelevante para outra.

Exemplo conceitual:

```yaml
governance:
  mode: governed
  scope:
    - climate-products
    - agroclimatic-analysis
  not_blocking:
    - core-authentication
    - project-management
```

Esse modelo evita que uma falha meteorológica bloqueie autenticação, projetos ou outras capacidades independentes.

### Princípio

> O poder de bloqueio deve acompanhar a dependência real, não apenas a existência do componente.

---

## 10. Critérios para transição de `shadow` para `governed`

A mudança exige três avaliações independentes.

## 10.1 Maturidade técnica

- checks estáveis;
- resultados reprodutíveis;
- contratos versionados;
- cobertura suficiente;
- observabilidade;
- diagnóstico confiável;
- baixo índice de falsos positivos;
- histórico de execução consistente.

## 10.2 Criticidade arquitetural

- dependência real do Core ou de uma capacidade;
- impacto conhecido sobre dados e decisões;
- impossibilidade de operação coerente sem o componente;
- risco de incompatibilidade;
- autoridade sobre domínio relevante;
- necessidade de bloqueio comprovada.

## 10.3 Governança organizacional

- responsável definido;
- capacidade de resposta;
- SLA ou compromisso operacional;
- processo de exceção;
- processo de suspensão;
- aprovação formal;
- rollback previsto;
- comunicação de incidentes.

### Decisão

Um componente só deve tornar-se `governed` quando:

```text
maturidade técnica
        +
criticidade arquitetural
        +
governança organizacional
        =
autoridade de bloqueio justificada
```

Maturidade isolada não é suficiente.

---

## 11. Caso de referência: SisTer-Clima

Linha de evolução recomendada:

```text
ETAPA 1 — shadow / pre-alpha
Objetivo: integrar o componente e observar sua participação.

ETAPA 2 — shadow / alpha
Objetivo: estabilizar checks, contratos e evidências.

ETAPA 3 — shadow / maturidade superior
Objetivo: comprovar confiabilidade operacional.

ETAPA 4 — decisão de criticidade
Objetivo: decidir se sua falha deve bloquear alguma capacidade.
```

Possíveis destinos:

```text
Clima informativo
→ permanece shadow

Clima necessário para capacidades agroclimáticas
→ governed apenas nesse escopo

Clima estrutural para todo o SisTer
→ governed globalmente, se isso for demonstrado
```

A promoção não deve ocorrer por automatismo. O estado final pode ser `shadow` permanente, e isso pode ser arquiteturalmente correto.

---

## 12. Procedimentos operacionais

## 12.1 Durante o desenvolvimento do motor

```text
1. Criar ou alterar o check declarativo.
2. Executar com --engine declarative.
3. Validar evidências e códigos de saída.
4. Executar com --engine compare.
5. Investigar qualquer divergência.
6. Registrar divergências intencionais.
7. Manter compare como padrão durante a transição.
```

## 12.2 Quando o componente está em `shadow`

```text
1. Executar todos os checks.
2. Registrar PASS, FAIL, SKIP e ERROR.
3. Exibir o resultado no SGR.
4. Não bloquear promoção fora do escopo.
5. Abrir pendência quando necessário.
6. Acompanhar recorrência.
7. Revisar periodicamente a classificação.
```

## 12.3 Antes de torná-lo `governed`

```text
1. Confirmar maturidade técnica.
2. Confirmar criticidade arquitetural.
3. Definir responsável operacional.
4. Simular falhas e bloqueios.
5. Avaliar impacto sobre a esteira.
6. Aprovar formalmente.
7. Versionar o perfil.
8. Registrar data e justificativa.
9. Definir rollback e exceções.
```

## 12.4 Em incidente envolvendo componente `governed`

```text
1. Identificar o check bloqueante.
2. Preservar evidências.
3. Confirmar se a falha é real ou do verificador.
4. Avaliar o escopo afetado.
5. Corrigir ou aplicar exceção formal.
6. Reexecutar o gate.
7. Registrar causa, decisão e resultado.
```

---

## 13. Métricas recomendadas

| Métrica | Finalidade |
|---|---|
| Taxa de equivalência `legacy` × `declarative` | Medir prontidão para retirada do legado |
| Divergências por tipo | Identificar problemas de motor, perfil ou normalização |
| Taxa de PASS por componente `shadow` | Avaliar estabilidade |
| Falhas recorrentes em `shadow` | Detectar experimentalismo permanente |
| Falsos bloqueios em `governed` | Medir qualidade dos gates |
| Tempo médio para diagnosticar divergência | Avaliar operabilidade do SGR |
| Tempo médio para recuperar gate bloqueado | Avaliar resposta operacional |
| Promoções impedidas corretamente | Medir valor preventivo da governança |
| Exceções concedidas | Detectar fragilidade ou excesso de rigor |
| Cobertura de evidências | Medir auditabilidade |

---

## 14. Estratégia para retirada do `legacy`

O `legacy` poderá ser removido quando houver evidência de que:

1. o motor declarativo cobre todos os checks relevantes;
2. as divergências conhecidas foram resolvidas ou formalmente aceitas;
3. existe histórico suficiente de equivalência;
4. os perfis estão versionados;
5. a equipe consegue diagnosticar falhas sem depender do motor antigo;
6. os testes de regressão preservam a semântica necessária;
7. a decisão de retirada foi registrada.

Após a retirada:

```text
estado transitório
compare + legacy + declarative

estado de destino
declarative
```

O modo `compare` perde sua função quando deixa de existir uma implementação alternativa a comparar.

---

## 15. Registros de decisão

Mudanças nos seguintes itens devem gerar registro arquitetural:

- alteração de `governance_mode`;
- mudança do escopo bloqueante;
- aceitação de divergência;
- retirada de check;
- alteração de severidade;
- concessão de exceção;
- promoção de `shadow` para `governed`;
- retirada do `legacy`;
- mudança do engine padrão.

Modelo mínimo:

```yaml
decision:
  id: ADR-SGR-000
  date: YYYY-MM-DD
  component: sister-clima
  subject: governance-mode
  previous: shadow
  new: governed
  scope:
    - climate-products
  rationale: >
    Justificativa técnica, arquitetural e organizacional.
  evidence:
    - historical-pass-rate
    - contract-version
    - failure-simulation
  approvers:
    - role-or-team
  rollback:
    procedure: >
      Procedimento para retorno ao estado anterior.
```

---

## 16. Política sintética

### Política de engine

- `compare` é o padrão durante a migração;
- `declarative` é o motor de destino;
- `legacy` é recurso temporário de diagnóstico;
- divergências exigem investigação e registro.

### Política de governança

- `shadow` observa sem bloquear;
- `governed` pode bloquear no escopo definido;
- mudança de modo exige decisão formal;
- maturidade não implica automaticamente criticidade;
- o poder de bloqueio deve acompanhar dependências reais.

---

## 17. Conclusão

Os modos do SGR materializam duas proteções complementares:

1. **proteção da mudança interna do verificador**, realizada por `legacy`, `declarative` e `compare`;
2. **proteção da evolução federada do ecossistema**, realizada por `shadow` e `governed`.

O resultado é um processo de produção capaz de:

- experimentar sem desorganizar;
- bloquear quando a coerência realmente está em risco;
- preservar evidências;
- limitar o raio de impacto;
- aprender com falhas;
- evoluir sem esconder transições.

Em termos de resiliência:

> **O SisTer não busca impedir toda perturbação; busca permanecer coerente enquanto observa, limita, registra e governa sua própria reconfiguração.**
