# SEC-02V — Checklist de validação da identidade interna assinada

**Estado:** pronto; validação formal ainda não executada

**Dependências:** publicação de SEC-01C/01D em `v0.2.6` e revisão do
MAES-SisTer/1.0

**Ameaças:** `TH-IDENT-01`, `TH-AUTHZ-01` e `TH-AUD-01`

Este cartão valida a implementação existente; não autoriza reimplementação nem
implantação antecipada.

## Emissão pelo `sisterd`

- [ ] `iss` identifica o `sisterd`.
- [ ] `sub` identifica o ator autorizado.
- [ ] `aud` restringe exclusivamente o consumidor.
- [ ] capacidades são mínimas para a chamada.
- [ ] finalidade é obrigatória e compatível.
- [ ] `iat` e `exp` respeitam a janela permitida.
- [ ] `jti` possui unicidade demonstrada.
- [ ] `request_id` é preservado ponta a ponta.
- [ ] cookie humano e token de sessão não são encaminhados.

## Criptografia e chaves

- [ ] algoritmo aceito é fixo e não escolhido livremente pela mensagem.
- [ ] chave privada exige caminho absoluto e permissões restritivas.
- [ ] ausência de chave impede a integração.
- [ ] chave pública é distribuída por procedimento governado.
- [ ] `kid` seleciona chave conhecida e permite rotação.
- [ ] chave desconhecida falha fechada.
- [ ] material criptográfico e asserção completa não aparecem em logs.

## Validação no Nexo

- [ ] assinatura alterada é rejeitada.
- [ ] audiência incorreta é rejeitada.
- [ ] token expirado é rejeitado.
- [ ] capacidade ausente é rejeitada.
- [ ] finalidade incompatível é rejeitada.
- [ ] emissor desconhecido é rejeitado.
- [ ] headers externos de identidade são ignorados.
- [ ] validação ocorre antes da regra de domínio.

## Repetição

- [ ] decisão documentada entre validade curta com idempotência e validade curta
  com cache de `jti`.
- [ ] comportamento durante reinício e concorrência é testado.
- [ ] risco residual é aceito ou bloqueia capacidades não idempotentes.

## Evidência necessária para conclusão

- [ ] contrato e schema validados.
- [ ] ADR-0018 revisada contra o MAES.
- [ ] testes do emissor aprovados.
- [ ] testes do consumidor aprovados.
- [ ] teste ponta a ponta `sisterd` → Nexo aprovado.
- [ ] evidência sanitizada, com ambiente e commits definitivos.
- [ ] risco residual e owners atualizados no MAES-SisTer/1.0.

SEC-02 somente muda para concluído quando todos os itens aplicáveis estiverem
comprovados. Até lá, a integração permanece sem autorização de implantação em
produção.
