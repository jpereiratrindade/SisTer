# Perfil executável de segurança da fronteira HTTP

**Identificador:** `sister.gateway-security-profile/1.1.0`

**Gate:** SEC-03C

**Estado:** SEC-03B encerrado como `LAB_PROVEN_WITH_RESTRICTIONS`; ainda não implantado

**Decisão:** [ADR-0020](../adr/ADR-0020-specialized-http-gateway.md)

## Artefatos normativos

Este documento explica o perfil. Os valores que a implementação deve consumir
e provar estão em:

- `ops/gateway/security-profile.json` — instância normativa;
- `contracts/gateway_security_profile.schema.json` — forma contratual;
- `scripts/validate_gateway_security_profile.py` — invariantes executáveis;
- `tests/gateway_security_profile_test.py` — matriz negativa do perfil.

Uma alteração textual não modifica o controle enquanto a instância e o
validador não forem atualizados e testados. Uma alteração que reduza um limite,
protocolo ou gate de segurança exige revisão do MAES e nova decisão de risco.

## Configuração mínima proposta

| Dimensão | Baseline SEC-03 |
|---|---|
| Produto | HAProxy Community; linha 3.2.x, piso validado 3.2.22 e patch mantido mais recente |
| Processo | `sister-gateway`, configuração `root:sister-gateway` |
| Entrada | `443/tcp`, TLS 1.3, HTTP/1.1, Host exato |
| HTTP sem TLS | porta 80 fechada |
| Upstream | único e fixo: `127.0.0.1:8000`, HTTP/1.1 |
| WebSocket/Upgrade | handshake negado; campos isolados removidos |
| Headers | externos de identidade, origem e correlação removidos |
| Request ID | novo valor hexadecimal de 32 caracteres |
| Headers | 64 campos, 16 KiB agregados, alvo de 8 KiB |
| Corpo | 1 MiB global; 64 KiB em `/api/auth/*` |
| Taxa mínima recebida | alvo de 1 KiB/s; mecanismo ainda não comprovado |
| Resposta upstream | alvo de 16 MiB; mecanismo ainda não comprovado |
| Headers/corpo | deadlines absolutos de 5 s/10 s |
| Conexões | 1024 globais; 32 por origem |
| Rate limiting | global, origem, rota e login |
| HSTS | desligado até gate operacional próprio |

## Matriz executável de realizabilidade

`ops/gateway/security-profile.json` classifica requisitos e resultados como:

- `NATIVE_DOCUMENTED`: o manual identifica mecanismo nativo, ainda sem prova
  de processo;
- `PROVEN`, `PROVEN_BY_SAFE_NORMALIZATION`, `PROVEN_BY_REJECTION` e
  `PROVEN_BY_STRIPPING`: resultado reproduzido no laboratório;
- `ACCEPTED_LAB_DIVERGENCE`: divergência literal aceita com owner, escopo,
  risco e condição de reabertura;
- `DEFERRED_TO_SEC-03V` e `SEC-03C_PENDING`: controle preservado em gate futuro;
- `MECHANISM_UNPROVEN`: nenhum mecanismo simples foi aceito e o controle não
  pode ser declarado implementado.

Taxa mínima e limite de resposta começam em `MECHANISM_UNPROVEN`. O validador
impede promovê-los documentalmente para nativos, habilitar Lua ou admitir
módulos de terceiros. SEC-03B-R registrou equivalências seguras e uma exceção
restrita sem reinterpretar divergência como conformidade.

## Resolução do laboratório SEC-03B-R

- `Content-Length` válido e idêntico é normalizado para um único valor;
- `Content-Length` inválido ou divergente é rejeitado e não chega ao upstream;
- handshake Upgrade/WebSocket completo é rejeitado;
- campos hop-by-hop isolados são removidos antes de HTTP comum seguir;
- duas linhas Host divergentes são rejeitadas;
- duas linhas Host idênticas formam `ACCEPTED_LAB_DIVERGENCE` sob autoridade
  única e canônica.

A exceção de Host é reaberta por múltiplos hosts, certificados, backends,
destino dinâmico ou mudança de linha/representação HTTP. SEC-03V é o gate de
revisão. A resolução autoriza SEC-03C, mas não merge, release ou exposição.

## Política de confiança

O endereço TCP visto pelo `sisterd` será o gateway. A origem reconstruída é
metadado de transporte, não identidade e não capacidade. A confiança em
`X-Forwarded-*` e `X-Request-ID` depende conjuntamente de:

1. remoção de todo valor externo;
2. reconstrução pelo gateway;
3. upstream estático;
4. restrição do host para que somente o gateway alcance `127.0.0.1:8000`;
5. teste negativo que tente acesso local e externo direto.

Sem qualquer uma dessas provas, o `sisterd` deve ignorar os headers e manter o
comportamento atual.

## Matriz de ameaças e critérios de evidência

| Ameaça | Controle definido em SEC-03A | Teste obrigatório em SEC-03V | Risco até SEC-03V | Owner |
|---|---|---|---|---|
| `TH-HTTP-02` | HTTP estrito, enquadramento inequívoco e protocolos mínimos | CL duplicado, TE, CL+TE, whitespace e parser diferencial | configuração ainda não implantada | gateway e transporte |
| `TH-HTTP-03` | limites, deadlines, conexões e taxas | Slowloris, saturação, corpo grande e upstream lento | valores ainda não calibrados sob carga | operação do gateway |
| `TH-HTTP-04` | remoção e reconstrução de headers | identidade, origem e ID forjados | confiança ainda não habilitada no `sisterd` | gateway e `sisterd` |
| `TH-WS-01` | Upgrade e WebSocket negados | handshake e retenção recusados | código legado permanece em laboratório | arquitetura de transporte |
| `TH-PROXY-01` | único destino literal, sem resolver ou destino do cliente | tentativa de alterar Host, destino e caminho | isolamento local ainda não implantado | operação de plataforma |
| `TH-PROXY-02` | timeouts, fila e limite de resposta | upstream lento, indisponível e resposta excessiva | HA e streaming fora de escopo | gateway e `sisterd` |
| `TH-CONF-01` | validação offline e falha fechada | config, certificado e upstream inválidos | erro operacional antes do gate | operação de plataforma |
| `TH-AUD-01` | log sanitizado e ID gerado na borda | correlação ponta a ponta e busca por segredos | retenção e integridade ainda pendentes | observabilidade |

O estado de todas essas fichas é `PROFILE_DEFINED`, não
`CONTROLLED_BASELINE`. `docs/evidence/security/SEC-03V.md` será criado somente
quando os testes forem executados; a referência identifica o artefato futuro e
não declara sua existência atual.

## Rollback verificável

Antes de cada promoção devem existir hashes do pacote, configuração,
certificado público e unidade anteriores. O procedimento:

```text
parar novas promoções
→ restaurar conjunto anterior
→ validar configuração offline
→ reload controlado
→ health externo e interno
→ confirmar sisterd ainda em loopback
```

O fallback permitido é indisponibilidade externa. São proibidos bind público do
`sisterd`, abertura direta de `8000`, TLS enfraquecido, proxy legado ou
WebSocket.

## Critério de saída de SEC-03A

SEC-03A termina quando o perfil válido passa no pipeline, mutações inseguras são
rejeitadas pelos testes, controles sem mecanismo permanecem explicitamente
inconclusivos, ADR/MAES usam os mesmos identificadores e nenhum artefato afirma
que o gateway já está implantado. SEC-03B pode então materializar uma
configuração de laboratório sem ampliar o escopo funcional.
