# `sister.workspace-view/1.0.0`

Contrato da projeção de usuário servida por `GET /api/v1/workspace`.

A resposta contém somente superfícies de interação completas e autorizadas. A
declaração semântica pertence ao componente; o `public_url` é resolvido pela
infraestrutura; o `sisterd` combina esses dados com a autoridade do ator.

Runtime, binding, probe, gateway e deployment não fazem parte deste contrato.
