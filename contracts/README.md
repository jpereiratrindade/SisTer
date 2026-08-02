# Contratos SisTer

Esta pasta e a fonte de verdade dos contratos de integracao do SisTer.

Contratos iniciais:

- `gateway_security_profile.schema.json`: perfil executável de SEC-03A; a
  instância normativa em `ops/gateway/security-profile.json` não representa
  implantação antes de SEC-03B/C/V.
- `subsystem/1.0.0/`: contrato comum `sister.subsystem/1.0.0` para
  manifestos, saúde, prontidão, capacidades, identidade interna, erros,
  auditoria e superfície técnica de subsistemas.
- `system_manifest.schema.json`: declaracao de um sistema federado.
- `camposync_package.schema.json`: pacote `camposync.package/1.0.0`,
  transportado por API local ou por meio offline sem alterar sua semantica.
- `evidence.schema.json`: evidencia vinculada a objeto, sistema e proveniencia.
- `public_scope.schema.json`: classificacao publico, restrito e privado para dados, evidencias, embeddings e diagnosticos.
- `sister_studio_capabilities.schema.json`: descoberta restrita de capacidades e formatos do Sister-Studio.
- `sister_nexo_integration.schema.json`: descoberta e acesso restrito ao
  subsistema de governança científica SisTer Nexo.
- `sister_studio_health.schema.json`: disponibilidade sanitizada dos modulos do Sister-Studio.
- `sister_clima_governance.schema.json`: finalidade não comercial, acesso
  identificado, licenças, atribuição e promoção de resultados do Sister-Clima.
- `integration_agreement.schema.json`: proposta ou contraproposta bilateral,
  versionada e negociável entre sistemas autônomos.
- `integration_receipt.schema.json`: aceite, ativação e transições auditáveis
  vinculadas ao digest exato de um acordo.

Versoes estabilizadas devem ser copiadas para `contracts/versions/vX.Y.Z/`.

## Fronteira de compartilhamento

Cada sistema integrante deve declarar no manifesto:

- link de acesso direto a plataforma de origem, quando existir;
- o que pode ser compartilhado com o SisTer;
- o que e intrinseco ao sistema e deve permanecer explorado na propria plataforma;
- o que e publico, restrito, privado ou sensivel;
- como a oferta do sistema entra na cadeia dado, informacao, conhecimento e sabedoria.

Na relacao DIKW, cada sistema pode ofertar informacoes de seu dominio. Para o SisTer, essas informacoes chegam como dados contratados; apos validacao, cruzamento e interpretacao, podem gerar informacao integrada, conhecimento territorial e, em casos bem governados, apoio a sabedoria decisoria.
