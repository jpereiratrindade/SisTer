# `sister.capability-invocation/1.0.0`

> **Status: DRAFT / NOT RUNTIME-NORMATIVE**

Contrato candidato do ARC-01 para representar a solicitação e o resultado de
uma capability entre um caller autorizado e um participante.

O envelope não pressupõe mediador, mecanismo de comunicação ou topologia. Este
draft não é consumido pelo runtime e não autoriza nenhuma chamada. Bindings e
protocolos pertencem ao ARC-02.

## Artefatos

- `invocation.schema.json`: solicitação semântica de capability;
- `invocation-result.schema.json`: resultado, negação, falha ou cancelamento;
- `examples/nexo-to-praxis.json`: solicitação direta governada por relação;
- `examples/nexo-to-praxis-result.json`: resultado atribuível ao Praxis;
- `examples/invalid-invocation-with-endpoint.json`: prova negativa de
  acoplamento a endpoint.
