# Contratos SisTer

Esta pasta e a fonte de verdade dos contratos de integracao do SisTer.

## Normativo vigente

- `gateway_security_profile.schema.json`: perfil executável 1.1 da fronteira;
  SEC-03B está provado com restrições, mas a instância normativa em
  `ops/gateway/security-profile.json` não representa implantação antes de
  SEC-03V após o fechamento restrito de ISO-01.
- `subsystem/1.0.0/`: contrato comum `sister.subsystem/1.0.0` para
  manifestos, saúde, prontidão, capacidades, identidade interna, erros,
  auditoria e superfície técnica de subsistemas.
- `system_manifest.schema.json`: declaracao de um sistema federado.
- `evidence.schema.json`: evidencia vinculada a objeto, sistema e proveniencia.
- `public_scope.schema.json`: classificacao publico, restrito e privado para dados, evidencias, embeddings e diagnosticos.
- `integration_agreement.schema.json`: proposta ou contraproposta bilateral,
  versionada e negociável entre sistemas autônomos.
- `integration_receipt.schema.json`: aceite, ativação e transições auditáveis
  vinculadas ao digest exato de um acordo.

## Histórico preservado e candidatos em quarentena

`camposync_package.schema.json` e os contratos com nomes específicos de Clima,
Nexo e Studio permanecem como memória arquitetural ou material candidato. Eles
não são contratos operacionais vigentes, não autorizam rotas e não substituem
o contrato comum. A classificação completa está em
[`docs/governance/ARTIFACT_STATUS.md`](../docs/governance/ARTIFACT_STATUS.md).

Versoes estabilizadas devem ser copiadas para `contracts/versions/vX.Y.Z/`.

## Fronteira de compartilhamento

Cada sistema integrante deve declarar no manifesto:

- link de acesso direto a plataforma de origem, quando existir;
- o que pode ser compartilhado com o SisTer;
- o que e intrinseco ao sistema e deve permanecer explorado na propria plataforma;
- o que e publico, restrito, privado ou sensivel;
- como a oferta do sistema entra na cadeia dado, informacao, conhecimento e sabedoria.

Na relacao DIKW, cada sistema pode ofertar informacoes de seu dominio. Para o SisTer, essas informacoes chegam como dados contratados; apos validacao, cruzamento e interpretacao, podem gerar informacao integrada, conhecimento territorial e, em casos bem governados, apoio a sabedoria decisoria.
