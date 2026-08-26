# ADR-0028: Fronteira entre componente, runtime e implantação

## Status

Aceita — define a fronteira normativa de qualificação e execução para
`sister.component/1.0.0` e `sister.runtime/1.0.0`.

Esta ADR não promove os contratos semânticos do ARC-01, não altera a vigência de
`sister.subsystem/1.0.0` e não autoriza, por si só, novos bindings, rotas,
exposição externa ou promoção de subsistemas reais.

## Contexto

A evolução do SisTer mostrou que conhecimento específico de sistemas concretos
não deve ser replicado em scripts de workstation, gateway, TLS, `NO_PROXY`,
verificação e ciclo de vida.

Quando cada camada conhece previamente Nexo, Praxis, URT ou qualquer outro
sistema, a composição passa a depender de listas implícitas e dispersas. Isso
permite inconsistências em que um participante é conhecido por uma parte da
implantação e esquecido por outra.

Ao mesmo tempo, o ARC-01 estabeleceu que identidade, autoridade, capacidades e
relações pertencem ao plano semântico e não devem depender de host, porta,
path, endpoint, protocolo ou intermediário técnico.

Era necessário definir uma fronteira complementar para responder a três
questões diferentes:

1. como uma árvore de código é qualificada como componente;
2. como um artefato já qualificado é iniciado e observado;
3. quem decide se, onde e por qual binding esse componente participa de uma
   implantação concreta.

## Decisão

Separar quatro responsabilidades.

### Participante

O contrato semântico descreve quem o sistema é, sobre o que possui autoridade,
o que pode oferecer e sob quais relações e responsabilidades participa.

A evolução desse plano continua governada pelo ARC-01. Esta ADR não promove
`sister.participant/2.0.0`, `sister.capability-invocation/1.0.0` ou
`sister.relation/1.0.0`.

### Componente

`sister.component/1.0.0` descreve como uma árvore de código pode ser qualificada
para composição.

O descritor pode declarar:

- identidade técnica do componente;
- sistema ao qual o componente pertence;
- papel arquitetural de implantação;
- referência ao contrato semântico aplicável;
- driver tipado de build e teste;
- artefatos produzidos;
- contrato de runtime.

O descritor não declara:

- host, porta, endereço, URL ou binding concreto;
- comandos shell arbitrários;
- autorização de implantação;
- elegibilidade para workstation ou produção.

Autodescrição não constitui auto-admissão.

### Runtime

`sister.runtime/1.0.0` descreve como um artefato previamente qualificado pode
ser operado.

A interface mínima é composta pelas operações semânticas:

- `start`;
- `stop`;
- `restart`;
- `status`;
- `health`.

`readiness` é opcional.

Essas operações não definem transporte. HTTP, TCP, socket Unix, IPC ou outra
técnica são decisões de realização ou binding e não fazem parte da ontologia
mínima do runtime.

O runtime não compila nem qualifica a árvore durante `start` e não incorpora
estado persistente à release.

### Implantação

A implantação seleciona componentes, aplica política, decide admissão, resolve
bindings concretos e materializa uma composição verificável.

Pertencem à implantação, e não ao descritor do componente:

- elegibilidade contextual;
- autorização de composição;
- host e porta;
- socket e caminhos operacionais concretos;
- variáveis e bindings de ambiente;
- exposição no gateway;
- TLS;
- roteamento;
- release resolvida.

O plano de implantação pode conhecer os componentes escolhidos para uma
realização concreta, mas o contrato genérico de componente não conhece
antecipadamente quais outros sistemas existirão no ecossistema.

## Invariantes arquiteturais

A decisão pode ser resumida por:

```text
autodescrição   != auto-admissão
descoberta      != confiança
compatibilidade != autorização
runtime         != transporte
binding         != identidade
composição      != perda de autonomia
```

E pela decomposição:

```text
PARTICIPANT
    quem sou e pelo que respondo

COMPONENT
    como meu software é qualificado

RUNTIME
    como meu artefato vive e é observado

DEPLOYMENT
    se, onde e como sou composto
```

## Relação com decisões existentes

- complementa a ADR-0027 ao definir uma fronteira operacional sem promover os
  contratos semânticos do ARC-01;
- preserva a ADR-0020: gateway especializado, TLS e borda externa continuam
  responsabilidades de implantação;
- preserva a ADR-0021: socket Unix continua sendo uma decisão válida de binding
  para a realização corrente, mas não um requisito constitutivo de runtime;
- preserva a quarentena da ADR-0022;
- não altera as fronteiras de identidade e autorização definidas pelas
  ADR-0018, ADR-0016 e ADR-0026.

## Consequências

### Positivas

- novos sistemas podem ser compostos sem introduzir nomes específicos no
  contrato genérico;
- build, runtime e implantação passam a ter responsabilidades verificáveis;
- um componente não pode se declarar autorizado ou elegível para produção;
- health e readiness deixam de tornar HTTP constitutivo;
- o plano de implantação pode derivar gateway, TLS, listeners e verificações de
  uma composição resolvida;
- a mesma semântica de runtime pode ser materializada por bindings diferentes.

### Custos e riscos

- `sister-infra` ainda precisa evoluir para consumir descritores e resolver
  composições declarativamente;
- sistemas existentes precisarão adotar `.sister/component.json` e a interface
  de runtime de forma incremental;
- drivers tipados de build e teste precisarão ser ampliados quando surgirem
  toolchains legítimos além dos inicialmente reconhecidos;
- a convivência entre `sister.subsystem/1.0.0` e os drafts do ARC-01 permanece
  até decisão específica de promoção semântica.

## Evidência de aceitação

Em 26 de agosto de 2026, a árvore isolada de build usada para esta decisão
produziu:

- build completo sem erro;
- `component_runtime_contract_tests`: PASS;
- suíte CTest: 32 testes registrados, 0 falhas;
- 25 testes executados com PASS;
- 7 testes de gateway marcados como `Skipped` por dependerem do ambiente
  apropriado;
- `git diff --check`: sem erros.

Os testes negativos verificam, entre outros pontos:

- rejeição de binding no descritor de componente;
- rejeição de comandos shell arbitrários;
- rejeição de caminhos que escapem da árvore;
- rejeição de ações de runtime não reconhecidas;
- ausência de auto-admissão por `eligibility`;
- neutralidade do contrato de runtime em relação a transporte;
- obrigatoriedade de `health`;
- opcionalidade de `readiness`.

## Próximos passos

1. publicar os contratos e esta ADR em um commit normativo;
2. atualizar a apresentação arquitetural do README principal em commit
   separado;
3. usar o URT como primeiro sistema real a demonstrar a nova fronteira;
4. evoluir `sister-infra` para resolver composição, política, bindings e release
   sem listas específicas de sistemas.
