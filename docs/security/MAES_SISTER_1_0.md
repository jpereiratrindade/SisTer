# MAES-SisTer/1.0 — Modelo de Ameaças e Estratégia de Segurança

**Identificador:** MAES-SisTer/1.0

**Estado:** aprovado e publicado na baseline `v0.2.6`

**Referência normativa:** EFE-SisTer/1.2

**Escopo inicial:** `sisterd`, controles SEC-00 a SEC-01D e ameaças que
governam o candidato posterior SEC-02

**Data de revisão:** 1 de agosto de 2026

**Autoridade aprovadora:** Coordenação do Projeto SisTer

**Owners confirmados:** manutenção do `sisterd`, arquitetura de segurança,
operação de plataforma e manutenção do Nexo, conforme cada ficha

## Finalidade

Este documento mantém o registro operacional exigido pela EFE-SisTer/1.2. Ele
relaciona ameaças aplicáveis, ativos, superfícies, controles, testes,
evidências, riscos residuais, responsáveis e estado. ADRs explicam decisões e
evidências registram execuções; nenhum deles substitui este modelo.

## Estados

| Estado | Significado |
|---|---|
| `CONTROLLED_BASELINE` | controle publicado e sustentado pela baseline indicada |
| `PARTIALLY_CONTROLLED` | há controles efetivos, mas parte relevante do cenário permanece residual |
| `VALIDATION_PENDING` | capacidade não publicada; candidato posterior aguarda gate formal |

## Registro inicial

### TH-CONF-01 — Exposição pública acidental

- **Ativo afetado:** plano de controle, credenciais e APIs administrativas.
- **Superfície:** configuração de bind, bootstrap e proxies legados.
- **Cenário:** produção inicia em endereço público ou habilita transporte legado.
- **Controles:** loopback obrigatório, bootstrap HTTP proibido e proxies
  HTTP/WebSocket com falha fechada em produção.
- **Testes:** `tests/sisterd_transport_quarantine_test.py` e
  `tests/sisterd_systemd_unit_test.py`.
- **Evidências:** ADR-0015, baseline `v0.2.5` e
  `docs/evidence/alpha/security.md`.
- **Risco residual:** erro operacional fora da configuração governada e ausência
  do gateway definitivo; não autoriza exposição direta.
- **Owner:** manutenção do `sisterd` e operação de plataforma.
- **Estado:** `CONTROLLED_BASELINE`.

### TH-AUTHZ-01 — Rota sem autorização ou autorização excessiva

- **Ativo afetado:** identidades, contratos, evidências e operações
  administrativas.
- **Superfície:** roteamento e decisão de autorização do `sisterd`.
- **Cenário:** rota sensível não declara política ou reinterpreta papel no
  handler.
- **Controles:** política explícita na entrada, capacidade mínima, negação por
  padrão e log correlacionado de decisão.
- **Testes:** `tests/sisterd_maturity_api_test.py`.
- **Evidências:** ADR-0016 e baseline `v0.2.5`.
- **Risco residual:** finalidade e recurso ainda são registrados, mas a decisão
  corrente avalia principalmente a capacidade declarada.
- **Owner:** arquitetura de autorização e manutenção do `sisterd`.
- **Estado:** `CONTROLLED_BASELINE`.

### TH-AUTH-01 — Força bruta, enumeração e abuso do login

- **Ativo afetado:** credenciais, sessões e disponibilidade do login.
- **Superfície:** `POST /api/auth/login`.
- **Cenário:** mudança de porta, IP ou identidade contorna contenção e cria
  memória sem limite.
- **Controles:** limites independentes por IP sem porta, identidade normalizada,
  par IP+identidade e processo; capacidade limitada, expiração, LRU e resposta
  uniforme `429` com `Retry-After`.
- **Testes:** `tests/security_hardening_tests.cpp` e
  `tests/sisterd_http_hardening_test.py`.
- **Evidências:** ADR-0019 e `docs/evidence/security/SEC-01C-01D.md`.
- **Risco residual:** endereços observados são locais até existir gateway
  confiável; contenção externa e distribuição entre processos pertencem ao
  SEC-03 e à evolução operacional.
- **Owner:** manutenção de autenticação do `sisterd`.
- **Estado:** `CONTROLLED_BASELINE` em `v0.2.6`.

### TH-HTTP-01 — Parsing e enquadramento HTTP inválidos

- **Ativo afetado:** disponibilidade e integridade do protocolo interno.
- **Superfície:** leitura de headers e corpo pelo parser HTTP próprio.
- **Cenário:** `Content-Length` inválido, duplicado, ambíguo, acima do limite ou
  em overflow atravessa o worker.
- **Controles:** parser decimal sem exceções, limite de 16 MiB, rejeição de
  duplicados, respostas controladas `400/413` e encerramento da conexão.
- **Testes:** `tests/security_hardening_tests.cpp` e
  `tests/sisterd_http_hardening_test.py`.
- **Evidências:** ADR-0019 e `docs/evidence/security/SEC-01C-01D.md`.
- **Risco residual:** o parser não pretende conformidade de servidor HTTP
  generalista; normalização diferencial ficará no gateway.
- **Owner:** manutenção de transporte interno do `sisterd`.
- **Estado:** `CONTROLLED_BASELINE` em `v0.2.6`.

### TH-HTTP-03 — Exaustão de recursos HTTP

- **Ativo afetado:** workers, memória, conexões, descritores e disponibilidade.
- **Superfície:** conexões HTTP, corpos, fila de jobs e login.
- **Cenário:** corpo grande, requisição lenta ou cardinalidade de chaves esgota
  recursos.
- **Controles:** tamanho máximo de corpo, fila e workers limitados, timeouts de
  socket, buckets limitados, expiração e LRU.
- **Testes:** `tests/security_hardening_tests.cpp` e
  `tests/sisterd_http_hardening_test.py`.
- **Evidências:** ADR-0019 e `docs/evidence/security/SEC-01C-01D.md`.
- **Risco residual:** timeouts de socket não contêm Slowloris integralmente;
  deadlines absolutos, taxa mínima e quotas de borda pertencem ao SEC-03.
- **Owner:** manutenção do `sisterd`; operação do gateway para o residual.
- **Estado:** `PARTIALLY_CONTROLLED`.

### TH-CXX-02 — Exceção encerra worker ou processo

- **Ativo afetado:** disponibilidade do plano de controle.
- **Superfície:** parser, handlers e pool de conexões.
- **Cenário:** entrada externa ou falha inesperada propaga exceção para fora do
  job.
- **Controles:** tradução local de erros esperados, barreira final para
  `std::exception` e exceções desconhecidas, fechamento pelo pool e continuidade
  do worker.
- **Testes:** `tests/security_hardening_tests.cpp` e health posterior a entradas
  hostis em `tests/sisterd_http_hardening_test.py`.
- **Evidências:** ADR-0019 e `docs/evidence/security/SEC-01C-01D.md`.
- **Risco residual:** falhas fatais, corrupção de memória e comportamento
  indefinido não são convertidos em exceções; UBSan ainda não foi executado.
- **Owner:** manutenção C++ do `sisterd`.
- **Estado:** `CONTROLLED_BASELINE` em `v0.2.6`.

### TH-IDENT-01 — Identidade interna forjada ou reutilizada

- **Ativo afetado:** identidade do ator e autoridade nas operações do Nexo.
- **Superfície:** fronteira HTTP `sisterd`–Nexo.
- **Cenário:** cookie humano, header forjado, token sem audiência, assinatura
  inválida ou repetição é aceito pelo consumidor.
- **Controles validados:** asserção Ed25519 curta, algoritmo fixo, `kid`,
  emissor, audiência, capacidade, finalidade, `iat`, `exp`, `jti`, `request_id`,
  contenção de repetição e construção limpa da requisição.
- **Testes:** emissor, consumidor, matriz HTTP negativa, rotação, reinício e
  ponta a ponta `sisterd`–Nexo–PostgreSQL.
- **Evidências:** `docs/evidence/security/SEC-02V.md`.
- **Risco residual:** cache de `jti` é local e perdido no reinício; distribuição
  e rotação de chaves são operacionais e ainda não foram exercitadas em deploy
  conjunto.
- **Owner:** manutenção de identidade do `sisterd` e manutenção do Nexo.
- **Estado:** `PARTIALLY_CONTROLLED`. Aprovado somente para leitura interna e
  shadow; `v0.2.6` permanece inalterada e não contém esta capacidade.

### TH-WS-01 — Retenção de recursos por WebSocket

- **Ativo afetado:** workers, conexões e disponibilidade do plano de controle.
- **Superfície:** proxy WebSocket legado.
- **Cenário:** conexão persistente ocupa worker ou permanece sem limites
  adequados.
- **Controles:** proxy proibido com falha fechada em produção e permitido apenas
  por habilitação explícita no laboratório.
- **Testes:** `tests/sisterd_transport_quarantine_test.py`.
- **Evidências:** ADR-0015 e baseline `v0.2.5`.
- **Risco residual:** código legado ainda existe para caracterização em
  laboratório; WebSocket definitivo, quotas e prazos pertencem ao SEC-03.
- **Owner:** arquitetura de transporte e operação do gateway.
- **Estado:** `PARTIALLY_CONTROLLED`.

## Controles não executados

### UndefinedBehaviorSanitizer

- **Controle:** não executado.
- **Motivo:** `libubsan` ausente no ambiente de validação.
- **Impacto:** cobertura parcial de comportamento indefinido.
- **Tratamento:** preparar ambiente compatível e anexar o resultado à evidência
  antes de promoção que exija esse controle.

## Ordem governada

O trabalho corrente mantém no máximo dois cartões simultâneos:

| Estado | Cartão |
|---|---|
| Concluído na baseline | fechamento de SEC-01C/01D em `v0.2.6` |
| Concluído na baseline | `SEC-GOV-00` — MAES-SisTer/1.0 |
| Concluído com restrição | `SEC-02V` — identidade interna read-only e shadow |
| Backlog imediato | `SEC-03` — gateway especializado |
| Backlog seguinte | `FED-01` — registro persistente de sistemas |

Perda de controle, validade ou evidência pode regredir maturidade, suspender a
capacidade ou bloquear a integração.

## Decisão de risco da baseline

A Coordenação do Projeto SisTer aprova os owners e estados acima para a
`v0.2.6`, com aceitação restrita dos seguintes riscos residuais:

- Slowloris, deadlines absolutos e quotas de borda permanecem em
  `TH-HTTP-03`, desde que o `sisterd` continue restrito a loopback e sem papel de
  servidor HTTP público até SEC-03.
- A contenção de login usa o endereço diretamente observado; nenhuma confiança
  em origem encaminhada existe antes do gateway governado.
- O proxy WebSocket legado permanece fisicamente presente apenas para
  laboratório, desabilitado e proibido em produção.
- A ausência de execução do UBSan limita a evidência sobre comportamento
  indefinido e deve ser sanada antes de gate que exija essa cobertura; não é
  ocultada nem classificada como falha funcional.

Não há aceitação de risco que autorize SEC-02 na release. `TH-IDENT-01` continua
em `VALIDATION_PENDING`, e capacidades de identidade assinada permanecem fora
da `v0.2.6`. Esta aprovação publica uma baseline interna de controles; não
declara prontidão para produção externa.
