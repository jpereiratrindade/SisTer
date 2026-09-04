# Projeção semântica do ecossistema 1.0.0

Este contrato descreve uma projeção de leitura do SisTer; ele não transfere ao
SisTer autoridade sobre identidades, capacidades ou estados pertencentes aos
participantes.

`SISTER_SEMANTIC_ECOSYSTEM_PROJECTION_FILE` pode apontar para um snapshot TSV
materializado por uma fonte competente. O formato é:

```text
META\tsister.semantic-ecosystem-source/1.0.0\t<revision>
PARTICIPANT\t<participant_id>\t<label>\t<declared_state>\t<authority_scope>\t<provenance_ref>
CAPABILITY\t<participant_id>\t<capability_id>\t<label>\t<authority_scope>
```

Sem arquivo configurado, arquivo indisponível ou cabeçalho inválido, a projeção
falha fechada e não infere participantes a partir do deployment. Relações ficam
explicitamente indisponíveis porque não existe hoje fonte runtime-normative para
elas. O endpoint de leitura é `GET /api/v1/ecosystem/semantic`.
