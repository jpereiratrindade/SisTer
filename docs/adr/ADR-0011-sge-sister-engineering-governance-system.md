# ADR-0011: Sistema de Governança da Engenharia do SisTer

## Status

Aceita

## Contexto

A validação do protótipo integrado demonstrou autenticação central, acesso
unificado e integração inicial com subsistemas. A próxima fase não deve ser
conduzida por funcionalidades isoladas, porque isso tende a espalhar decisões
arquiteturais, contratos e evidências em artefatos desconectados.

O SisTer já possui ADRs, contratos, gates verificáveis, verificador de
maturidade, evidências e Centro de Engenharia. Falta nomear e governar esse
conjunto como um sistema explícito.

## Decisão

Adotar o **Sistema de Governança da Engenharia do SisTer (SGE-SisTer)** como
plano de controle da evolução técnica da plataforma.

O SGE-SisTer compreende:

- ADRs e documentos de arquitetura;
- contratos versionados;
- pacotes de trabalho vinculados ao roteiro de maturidade;
- gates de engenharia;
- verificador de maturidade;
- evidências e aprovações;
- Centro de Engenharia do SisTer;
- critérios de promoção de estágio.

A partir desta decisão, uma nova funcionalidade ou integração deve declarar em
qual pacote de trabalho, ADR ou decisão arquitetural e gate de engenharia se
encaixa. Quando essa relação ainda não existir, a lacuna deve ser registrada
antes da implementação.

## Invariantes

- O verificador continua sendo a autoridade automatizada sobre gates.
- O Centro de Engenharia apresenta evidências, mas não executa comandos nem
  aprova promoções.
- Contratos mudam por versão, com validação automatizada.
- Evidências operacionais e aprovações humanas permanecem rastreáveis.
- Promoções de estágio exigem artefato, teste, registro e responsável.
- Exceções arquiteturais devem ser temporárias, explícitas e revisáveis.

## Consequências

- O SisTer passa a evoluir por arquitetura governada, não por crescimento
  funcional desconectado.
- O plano de transição, o roteiro Alfa-Beta-Gama e o Centro de Engenharia
  formam uma cadeia única de governança.
- A equipe ganha uma pergunta de entrada para cada mudança: qual pacote de
  trabalho, qual decisão e qual gate justificam este incremento?
- O SGE-SisTer passa a ser componente administrativo da plataforma, mesmo que
  parte dele ainda viva em documentos e scripts.
- Mudanças rápidas continuam possíveis, mas precisam produzir rastro técnico
  proporcional ao risco.
