# ADR-0027: Separação entre plano de controle e plano de participação

## Status

Proposta — ARC-01; contratos associados em **DRAFT / NOT RUNTIME-NORMATIVE**.

Esta ADR não autoriza alteração de runtime, banco, gateway, deployment ou
transporte. Sua aceitação operacional depende dos experimentos e decisões
posteriores definidos abaixo.

## Contexto

O contrato vigente `sister.subsystem/1.0.0` comprovou uma integração técnica
controlada, porém representa participação por uma superfície HTTP canônica. A
avaliação de engenharia v0.2.0 concluiu que essa superfície é um binding
histórico, não a definição de participante ou capability.

A simples centralização de toda comunicação em `sisterd` também seria
incompatível com a autonomia pretendida. Ela transformaria uma superfície útil
em intermediário obrigatório e faria relações entre participantes dependerem
da presença do centro.

É necessário distinguir:

- funções que representam e controlam uma realização;
- interações pelas quais participantes compõem capacidades sob relações
  governadas.

## Decisão proposta

Separar conceitualmente dois planos.

### Plano de controle e superfície

`sisterd` pode oferecer, conforme a realização:

- Web/BFF e ações originadas nessa superfície;
- sessão humana e integração com autoridade de identidade nomeada;
- discovery e catálogo derivado;
- visão de relações;
- observações e correlação operacional.

Essas funções não tornam `sisterd` fonte da identidade, estado, política ou
autoridade de outro participante.

### Plano de participação

Participantes podem invocar capacidades uns dos outros quando uma `Relation`
definir participantes, papéis, finalidade, contratos, concessões, fronteiras
de autoridade e evidências.

A semântica da invocação deve ser válida entre caller e participante sem
pressupor um intermediário obrigatório. Topologia e bindings serão definidos
separadamente por relação e implantação.

### Contratos candidatos do ARC-01

Criar, sem vigência no runtime:

- `sister.participant/2.0.0`;
- `sister.capability-invocation/1.0.0`;
- `sister.relation/1.0.0`.

Os três contratos e todas as suas instâncias de exemplo carregam marcação
explícita `DRAFT` e `runtime_normative=false`.

Os contratos semânticos não definem host, porta, path, método, endpoint,
gateway, protocolo ou intermediário técnico. Contratos de binding pertencem ao
ARC-02 e só serão propostos depois da estabilidade semântica e do desenho do
experimento E3.

## Compatibilidade

`sister.subsystem/1.0.0` permanece normativo e imutável durante o ARC-01. Os
novos drafts não o substituem, não são aceitos pelo runtime e não promovem
subsistemas reais.

A transformação entre o contrato vigente e os drafts não é automática:
identidade e nomes podem ser projetados, mas capacidades precisam ser
enriquecidas com autoridade, propósito, contratos e evidência. Elementos HTTP
do contrato vigente não possuem equivalente nos contratos semânticos.

A matriz detalhada está em
[`contracts/compatibility/SUBSYSTEM_1.0.0_TO_ARC01_DRAFTS.md`](../../contracts/compatibility/SUBSYSTEM_1.0.0_TO_ARC01_DRAFTS.md).

## Relação com decisões existentes

- não supersede ADR-0020 nem ADR-0021; elas continuam governando a borda e o
  ingresso produtivo atuais;
- preserva a quarentena da ADR-0022;
- amplia o modelo conceitual da ADR-0023 sem alterar seu fluxo operacional;
- preserva a separação entre identidade e autorização das ADR-0018 e ADR-0026.

Uma publicação externa direta de adaptador de participante ampliaria a
fronteira qualificada pela ADR-0020 e exigiria ADR, threat model, testes
negativos, observabilidade e rollback próprios.

## Consequências

### Positivas

- participante, capability e relação tornam-se descritíveis sem transporte;
- `sisterd` pode centralizar a superfície sem centralizar a ecologia;
- relações diretas tornam-se representáveis sem transferir autoridade;
- o futuro experimento E3 pode comparar bindings sobre a mesma semântica.

### Custos e riscos

- haverá convivência temporária entre um contrato HTTP vigente e drafts
  semânticos;
- a migração exigirá enriquecimento, não simples conversão de campos;
- a ausência deliberada de bindings impede qualquer uso operacional no ARC-01;
- aceitar os drafts cedo demais criaria duas fontes normativas conflitantes.

## Gates

### ARC-01

- schemas e exemplos válidos;
- testes negativos contra vazamento de detalhes de binding;
- matriz explícita de compatibilidade;
- nenhuma alteração de runtime, banco, gateway ou deployment;
- todos os novos contratos permanecem draft e não normativos.

### ARC-02 — futuro, fora desta ADR

- definir o experimento E3;
- implementar bindings candidatos apenas no participante de referência;
- comparar equivalência semântica, falhas, deadlines e evidências;
- decidir se algum contrato de transporte merece estabilização.

## Evidência esperada para mudança de status

Esta ADR somente poderá avançar depois de revisão humana dos drafts, validação
dos schemas e confirmação de que não existe consumidor de runtime para os novos
identificadores contratuais.
