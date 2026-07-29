# ADR-0008 — Acordos bilaterais para sistemas autônomos

- Estado: aceito e implementado como referência Nexo–Compras
- Data: 2026-07-29

## Decisão

Integrações entre sistemas autônomos serão governadas por acordos bilaterais.
Cada participante mantém seu próprio Aggregate local, correlacionado por
`agreement_id`, revisão, perfil e digest SHA-256. Não existe Aggregate,
transação, tabela ou credencial compartilhada.

O protocolo comum é `sister.integration-agreement/1.0.0`. Ele define proposta,
contraproposta, negociação de capacidades, recibos, ativação, suspensão,
revogação e auditoria mínima. Perfis específicos definem operações, schemas,
finalidades e restrições de domínio.

Estados bilaterais e processamento técnico local são independentes. Mudanças
em proposta ou contraproposta criam nova revisão; aceitações nunca são
reescritas. A ativação exige um `AcceptanceReceipt` e um `ActivationReceipt`
para o mesmo identificador, revisão e digest.

## Identidade e confiança

O protocolo admite identidade local, provedor compartilhado ou federação. O
perfil Nexo–Compras usa inicialmente a identidade compartilhada do SisTer,
sem tornar essa escolha obrigatória para outros perfis.

Recibos da primeira versão registram emissor, operador, instante, revisão,
digest e encadeamento. Assinatura criptográfica permanece opcional até existir
uma infraestrutura real de chaves de sistema.

## Implementação de referência

O perfil `nexo-compras.profile/1.0.0` é a primeira implementação. Nexo e
Compras oferecem interfaces web para operar o mesmo ciclo, APIs contratuais,
armazenamento independente e trilhas locais correlacionadas. Após a validação
prática de outros perfis, o núcleo reutilizável poderá ser extraído
sem levar conceitos de projeto, atividade, necessidade ou fornecedor para o
protocolo comum.
