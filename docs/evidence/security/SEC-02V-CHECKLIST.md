# SEC-02V — Checklist de validação da identidade interna assinada

**Estado:** concluído; aprovado com restrição read-only e shadow

**Dependências:** publicação de SEC-01C/01D em `v0.2.6` e revisão do
MAES-SisTer/1.0

**Ameaças:** `TH-IDENT-01`, `TH-AUTHZ-01` e `TH-AUD-01`

Este cartão valida a implementação existente; não autoriza reimplementação nem
implantação antecipada.

## Emissão pelo `sisterd`

- [x] `iss` identifica o `sisterd`.
- [x] `sub` identifica o ator autorizado.
- [x] `aud` restringe exclusivamente o consumidor.
- [x] capacidades são mínimas para a chamada.
- [x] finalidade é obrigatória e compatível.
- [x] `iat` e `exp` respeitam a janela permitida.
- [x] `jti` possui unicidade demonstrada.
- [x] `request_id` é preservado ponta a ponta.
- [x] cookie humano e token de sessão não são encaminhados.

## Criptografia e chaves

- [x] algoritmo aceito é fixo e não escolhido livremente pela mensagem.
- [x] chave privada exige caminho absoluto e permissões restritivas.
- [x] ausência de chave impede a integração.
- [x] chave pública é distribuída por procedimento governado de teste.
- [x] `kid` seleciona chave conhecida e permite rotação.
- [x] chave desconhecida falha fechada.
- [x] material criptográfico e asserção completa não aparecem em logs.

## Validação no Nexo

- [x] assinatura alterada é rejeitada.
- [x] audiência incorreta é rejeitada.
- [x] token expirado é rejeitado.
- [x] capacidade ausente é rejeitada.
- [x] finalidade incompatível é rejeitada.
- [x] emissor desconhecido é rejeitado.
- [x] headers externos de identidade são ignorados.
- [x] validação ocorre antes da regra de domínio.

## Repetição

- [x] decisão documentada entre validade curta com idempotência e validade curta
  com cache de `jti`.
- [x] comportamento durante reinício e concorrência é testado.
- [x] risco residual bloqueia capacidades não idempotentes.

## Evidência necessária para conclusão

- [x] contrato e schema validados.
- [x] ADR-0018 revisada contra o MAES.
- [x] testes do emissor aprovados.
- [x] testes do consumidor aprovados.
- [x] teste ponta a ponta `sisterd` → Nexo aprovado.
- [x] evidência sanitizada, com ambiente e commits definitivos.
- [x] risco residual e owners atualizados no MAES-SisTer/1.0.

Consulte [`SEC-02V.md`](./SEC-02V.md). A conclusão é restrita: a integração não
possui autorização para escrita, produção externa ou exposição pública.
