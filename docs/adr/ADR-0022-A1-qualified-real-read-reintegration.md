# ADR-0022-A1 — Reintegração qualificada de leitura de subsistema real

## Status

**PROPOSTA / NÃO ACEITA AINDA.**

A aceitação depende do witness executável `WEB-CONTENT-02C-B2`. Este adendo não
promove ARC-01/ARC-02 a contrato runtime-normativo.

## Contexto

A ADR-0022 colocou integrações reais em `quarantined` para que a qualificação
do núcleo pudesse usar `sister_reference` como alvo normativo e previsível.
A saída da quarentena foi especificada conceitualmente, mas não foi
materializada como uma sequência operacional de reintegração read-only.

O Nexo hoje publica:

```text
GET /api/v1/context-projection
```

e aceita `Sister-Assertion` Ed25519 para a capacidade:

```text
nexo.context.read
```

preservando sua própria autoridade sobre identidade local, autorização e fatos.

## Decisão proposta

Autorizar uma única reintegração read-only originada pela superfície Web/BFF:

```text
ator autenticado no SisTer
        ↓
GET SisTer /api/v1/context-projection
        ↓
autorização local: workspace.context.read
        ↓
asserção Ed25519 emitida pelo sisterd
        ↓
GET Nexo /api/v1/context-projection
        ↓
autorização local do Nexo
        ↓
projeção factual
```

Política federada fixa:

```text
participant  = sister_nexo
audience     = sister_nexo
capability   = nexo.context.read
purpose      = research_operations
method       = GET
path         = /api/v1/context-projection
mutation     = none
```

`workspace.context.read` pertence ao SisTer e apenas autoriza solicitar a
projeção. `nexo.context.read` é transportada na asserção. O Nexo continua
responsável por resolver `sub` e decidir quais fatos retornar.

## Relação com a ADR-0018

A ADR-0018 continua sendo a autoridade para o **formato criptográfico e as
invariantes de identidade interna assinada**: JWS compacto, Ed25519, `kid`,
`iss`, `sub`, audiência, capacidades mínimas, finalidade, `iat`/`exp`, `jti`,
`request_id`, proteção da chave privada e não propagação de credenciais externas.

Entretanto, a política operacional histórica daquela baseline:

```text
GET /integrations/nexo/projects
capability = nexo.projects.read
feature flag = SISTER_ENABLE_NEXO_SIGNED_INTEGRATION
```

**não é reativada por este adendo**.

Para a reintegração qualificada definida aqui, essa política operacional é
substituída exclusivamente por:

```text
GET /api/v1/context-projection
capability local SisTer = workspace.context.read
capability federada     = nexo.context.read
feature flag             = SISTER_ENABLE_NEXO_CONTEXT_PROJECTION
```

Assim, este adendo reutiliza a primitive criptográfica qualificada pela
ADR-0018 sem restaurar a rota, a capability ou a feature flag históricas. A
distinção deve permanecer explícita para que patrimônio histórico não seja
confundido com superfície runtime ativa.

## Transporte

Não se restaura o `NexoClient` histórico e não se cria proxy genérico.

A primeira integração assinada real reutiliza somente primitives de transporte
já qualificadas no `sisterd`:

```text
connectLoopback
sendAll
timeouts
limite de resposta
```

Ela NÃO reutiliza `proxyToSubsystem`, porque esse caminho injeta identidade
legada (`X-Sister-*` e token interno) e pertence ao subsistema de referência.

Enquanto existir apenas uma integração assinada real, a composição da requisição
assinada permanece mínima e local. Uma abstração de transporte separada só deve
ser extraída quando houver uma segunda ocorrência real que prove a generalização.

## Binding

O host é uma invariante de segurança do runtime integrado:

```text
127.0.0.1
```

Não é introduzida uma segunda configuração de host.

A porta do Nexo é uma binding runtime derivada da autoridade de
composition/deployment e materializada pelo Infra:

```text
SISTER_NEXO_PORT
```

Quando a feature estiver habilitada, a ausência dessa binding falha fechada na
configuração. O código não assume `8015` como fallback.

## Invariantes

- feature desabilitada por padrão;
- nenhuma chamada ao Nexo sem sessão e `workspace.context.read`;
- `sub` deriva exclusivamente da sessão autenticada;
- `request_id` é gerado pelo `sisterd`;
- cada chamada recebe `jti` novo;
- cookie, Authorization externo e `X-Sister-*` do browser não atravessam;
- chave privada e asserção nunca são registradas;
- somente `GET`/`HEAD` da rota exata são aceitos;
- query string é recusada neste corte;
- resposta upstream é limitada;
- status upstream diferente de `200` não é confundido com sessão inválida;
- falha de transporte é registrada apenas por classe, sem `exception.what()`;
- o SisTer não persiste ou reidentifica a projeção;
- referências `authority + kind + id` retornam sem reconstrução;
- ARC-01 continua DRAFT / NOT RUNTIME-NORMATIVE.

## Fora de escopo

- escrita;
- ARC-02 runtime;
- proxy Nexo genérico;
- `NexoClient` histórico;
- cache;
- persistência da projeção;
- gateway;
- Home (`WEB-CONTENT-02C-B3`).

## Gates para aceitação

1. `sisterd` compila;
2. `sisterd_internal_assertion_tests` passa;
3. `sisterd_context_projection_tests` passa;
4. feature desabilitada retorna `404` sem upstream;
5. método inválido não abre upstream;
6. asserção contém `iss=sisterd`, `aud=sister_nexo`,
   `capabilities=["nexo.context.read"]`, `purpose=research_operations`;
7. `sub` coincide com o ator autenticado no SisTer;
8. `request_id` não é aceito do cliente;
9. duas chamadas produzem `jti` e `request_id` distintos;
10. cookie, Bearer e `X-Sister-*` não chegam ao Nexo;
11. asserção e chave privada não aparecem nos logs;
12. resposta factual conserva referências federadas;
13. witness real SisTer → Nexo retorna a projeção autorizada;
14. `SISTER_NEXO_PORT` observado no LAB é derivado da autoridade de
    deployment/composition;
15. `sub` resolve uma identidade já existente no Nexo sem fallback por
    nome, e-mail ou label.

Se o gate 15 falhar, B3 deve parar. A correção será binding explícito de
identidade, nunca inferência textual.

Somente após todos os gates este adendo pode mudar para **ACEITA**.
