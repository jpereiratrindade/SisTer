# `sister.participant/2.0.0`

> **Status: DRAFT / NOT RUNTIME-NORMATIVE**

Contrato candidato do ARC-01 para descrever um participante e suas capacidades
sem tornar qualquer mecanismo de comunicação parte de sua identidade.

Este draft não substitui `sister.subsystem/1.0.0`, não autoriza integração,
não publica bindings e não altera o runtime. A convivência e as lacunas entre
os contratos estão documentadas na
[matriz de compatibilidade](../../compatibility/SUBSYSTEM_1.0.0_TO_ARC01_DRAFTS.md).

## Artefatos

- `participant.schema.json`: identidade, ownership, autoridades, capacidades e
  papéis relacionais declarados pelo participante;
- `capability.schema.json`: semântica, contratos de entrada/saída, autoridade
  decisória, efeitos e evidências de uma capacidade;
- `examples/participant-nexo.json`: participante com capacidade de leitura;
- `examples/participant-praxis.json`: participante com capacidade de avaliação;
- `examples/invalid-participant-with-transport.json`: prova negativa de que
  detalhes de transporte não pertencem ao manifesto semântico.

## Limite do draft

Bindings serão tratados somente no ARC-02, depois da estabilização destes
contratos. A presença deste diretório no repositório não concede vigência
operacional.
