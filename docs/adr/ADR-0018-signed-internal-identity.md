# ADR-0018: Identidade interna assinada entre `sisterd` e subsistemas

## Status

Aceita e validada pelo SEC-02V para uso interno, read-only e shadow

## Contexto

Depois de autenticar a sessão humana e autorizar uma capacidade, o `sisterd`
precisa transmitir ao subsistema somente o contexto necessário à operação. O
protótipo usava cabeçalhos `X-Sister-*`, token estático opcional e, no túnel
WebSocket, o próprio cookie. Esses mecanismos não comprovam origem, audiência,
finalidade ou validade temporal e não podem ser promovidos.

SEC-02 deve provar a fronteira com um único consumidor, o SisTer Nexo, sem
reativar a integração em produção nem antecipar gateway, registro federativo ou
`IntegrationRun`.

A EFE-SisTer/1.2 classifica esta fronteira principalmente como `TH-IDENT-01`,
com relações a `TH-AUTHZ-01` e `TH-AUD-01`. A implementação não equivale à
promoção: depois da publicação de SEC-01C/01D em `v0.2.6`, o MAES-SisTer/1.0
deve registrar controles, testes, riscos residuais e responsáveis, e uma
validação formal deve autorizar ou bloquear a implantação conjunta com o Nexo.
O gate executável e seu resultado estão registrados no
[`SEC-02V`](../evidence/security/SEC-02V.md).

## Decisão

O `sisterd` emite uma asserção no formato JWS compacto, assinada com Ed25519. O
header protegido contém:

```json
{
  "alg": "EdDSA",
  "typ": "sister-internal+jwt",
  "kid": "identity-2026-08"
}
```

O payload segue
`sister.subsystem/1.0.0/identity-claims.schema.json` e contém obrigatoriamente:

- emissor `sisterd`;
- sujeito humano ou sistêmico;
- audiência exclusiva do consumidor;
- somente as capacidades necessárias à chamada;
- finalidade;
- emissão e expiração;
- identificador único `jti`;
- `request_id` de correlação ponta a ponta.

Na primeira fatia, o cliente Nexo usa audiência `sister_nexo`, capacidade
`nexo.projects.read`, finalidade `research_operations` e TTL padrão de 60
segundos. O TTL configurável nunca pode exceder 300 segundos.

A asserção é enviada em:

```text
Authorization: Sister-Assertion <JWS compacto>
```

O cliente específico do Nexo constrói a requisição do zero. Não encaminha
`Cookie`, `Authorization`, `X-Sister-*` nem `X-Request-ID` recebidos do cliente;
o `request_id` interno é gerado pelo `sisterd` e substitui qualquer valor externo.

## Chaves e rotação

- A chave privada Ed25519 é lida de caminho local explícito e absoluto por
  `SISTER_INTERNAL_IDENTITY_PRIVATE_KEY_FILE`.
- O arquivo privado deve ser regular e possuir permissão `0600` ou mais
  restritiva; configuração ausente, relativa, ilegível ou permissiva falha
  fechada antes da conexão com o Nexo.
- `SISTER_INTERNAL_IDENTITY_KEY_ID` identifica a chave ativa.
- O verificador mantém um conjunto de chaves públicas indexadas por `kid`.
- A rotação publica primeiro a nova chave pública, troca o `kid` do emissor e
  remove a chave anterior somente depois do maior TTL e da margem de relógio.
- Nesta etapa, a distribuição das chaves públicas é operacional, fora de banda
  e somente leitura. Serviço central de chaves e rotação automática ficam fora
  de escopo.

Exemplo de geração:

```bash
umask 077
openssl genpkey -algorithm Ed25519 -out /etc/sister/identity-private.pem
openssl pkey -in /etc/sister/identity-private.pem -pubout \
  -out /etc/sister/identity-public.pem
```

## Verificação e repetição

O verificador de referência valida, nesta ordem:

1. estrutura e limites do JWS;
2. algoritmo, tipo e `kid` protegido;
3. assinatura Ed25519;
4. emissor, audiência, finalidade e capacidade;
5. janela temporal e duração máxima;
6. unicidade de `jti` até a expiração.

O cache de repetição atual é local ao processo consumidor e podado após a
expiração. Reinício do consumidor perde esse cache; portanto, operações não
idempotentes ou de maior impacto ainda exigirão armazenamento compartilhado de
`jti` ou outra proteção transacional. Essa limitação é aceita nesta fatia curta
e deve ser revista antes de ampliar capacidades de escrita.

## Invariantes

- Autenticação e autorização ocorrem antes da emissão.
- Uma asserção é válida para uma audiência, finalidade e conjunto mínimo de
  capacidades.
- Cookie e token bruto de sessão nunca atravessam a fronteira Nexo.
- Cabeçalhos externos de identidade não são tratados como autoridade.
- Ausência ou falha da chave impede a chamada ao subsistema.
- Asserções completas e material privado nunca são registrados em logs.
- Chave desconhecida, assinatura alterada, expiração, escopo incompatível e
  repetição falham fechados.

## Consequências

- O `main.cpp` deixa de construir identidade específica do Nexo; o transporte
  fica encapsulado em `integrations/NexoClient` e a identidade em `identity/`.
- O Nexo incorpora o verificador de referência e uma política inicial para
  `GET /api/v1/projects`; a ativação operacional e a distribuição da chave
  pública devem acompanhar o deploy conjunto.
- O proxy genérico permanece apenas para Clima no laboratório; não é promovido.
- SEC-03 continua obrigatório antes de reabrir integrações em produção.

## Fora de escopo

- gateway definitivo e contenção de abuso;
- mTLS;
- registro federativo e acordos persistentes;
- `IntegrationRun` e proveniência completa;
- autorização científica complexa por finalidade;
- serviço central de chaves.
