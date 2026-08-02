# Evidência de promoção — SEC-02M

**Data:** 1 de agosto de 2026

**Release alvo:** `v0.2.7`

**Dependências:** SEC-02V aprovado, SisTer `v0.2.6` e contraparte validada do
Nexo

**Escopo autorizado:** interno, read-only e shadow

## Objetivo

Converter os limites aprovados em SEC-02V em comportamento executável antes da
incorporação ao `main`. SEC-02M não amplia a autoridade do cliente: separa a
integração assinada do proxy legado e restringe a emissão à política validada.

## Invariantes comprovados

- `SISTER_ENABLE_NEXO_SIGNED_INTEGRATION` é `false` por padrão;
- a flag é independente de `SISTER_ENABLE_LEGACY_PROXY` e
  `SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY`;
- ativar a integração não habilita Clima, WebSocket ou Nexo-Compras;
- chave ausente, caminho relativo, arquivo inválido, permissão excessiva ou
  `kid` inválido impedem o arranque antes do listener;
- o diagnóstico registra `nexo_signed_integration=enabled|disabled` e
  `nexo_signed_mode=read_only_shadow`, sem registrar chave ou asserção;
- somente a política abaixo cria o cliente, emite asserção e abre conexão:

```text
GET /integrations/nexo/projects
→ GET /api/v1/projects
→ nexo.projects.read
→ research_operations
```

- outro método ou caminho sob `/integrations/nexo` retorna `404` sem asserção e
  sem conexão ao Nexo.

## Testes executados

```bash
cmake -S . -B build -DSISTER_BUILD_TESTS=ON
cmake --build build -j2
ctest --test-dir build --output-on-failure
```

Resultado: **12/12 testes aprovados**.

O teste de processo `sisterd_nexo_identity_tests` executou adicionalmente:

1. chamada válida com os dois proxies legados desligados;
2. flag nova ausente, confirmando negação por padrão;
3. configuração sem chave, confirmando saída antes da abertura da porta;
4. `POST /integrations/nexo/projects`;
5. `GET /integrations/nexo/projects/other`;
6. `GET /integrations/nexo/compras/`;
7. `GET /integrations/nexo/`;
8. `GET /integrations/clima`.

Os casos 4 a 8 retornaram `404`; o listener sentinela do Nexo não recebeu
conexão. A chamada válida continuou produzindo somente a asserção mínima e foi
traduzida para `GET /api/v1/projects`.

## Decisão

**SEC-02M aprovado para incorporação coordenada na `v0.2.7`.** A promoção não
autoriza escrita, rota genérica, Nexo-Compras, exposição externa ou produção
plena. `TH-IDENT-01` permanece `PARTIALLY_CONTROLLED`; SEC-02R é gate obrigatório
antes de escrita e SEC-03 permanece obrigatório para a fronteira HTTP externa.
