# MAES-SisTer/1.0 — Modelo de Ameaças e Estratégia de Segurança

**Identificador:** MAES-SisTer/1.0

**Estado:** aprovado e atualizado na baseline `v0.2.7`

**Referência normativa:** EFE-SisTer/1.2

**Escopo inicial:** `sisterd`, controles SEC-00 a SEC-02M e perfil SEC-03A da
fronteira HTTP especializada

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
| `PROFILE_DEFINED` | requisito e teste são executáveis, mas o controle ainda não foi implantado nem validado em processo |

## Registro inicial

### TH-CONF-01 — Exposição pública acidental

- **Ativo afetado:** plano de controle, credenciais e APIs administrativas.
- **Superfície:** configuração de bind, bootstrap e proxies legados.
- **Cenário:** produção inicia em endereço público ou habilita transporte legado.
- **Controles:** loopback obrigatório, bootstrap HTTP proibido e proxies
  HTTP/WebSocket com falha fechada em produção; SEC-03A define porta externa,
  upstream fixo, validação offline e rollback sem reabrir o `sisterd`.
- **Testes:** `tests/sisterd_transport_quarantine_test.py` e
  `tests/sisterd_systemd_unit_test.py`; perfil em
  `tests/gateway_security_profile_test.py`.
- **Evidências:** ADR-0015, baseline `v0.2.5` e
  `docs/evidence/alpha/security.md`; ADR-0020 e perfil SEC-03A ainda não são
  evidência de implantação.
- **Risco residual:** o gateway ainda não está implantado; erro operacional fora
  da configuração governada não autoriza exposição direta.
- **Owner:** manutenção do `sisterd` e operação de plataforma.
- **Estado:** `CONTROLLED_BASELINE` para a quarentena do `sisterd`;
  `PROFILE_DEFINED` para o subcontrole de gateway.

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

### TH-HTTP-02 — Interpretação HTTP divergente na fronteira

- **Ativo afetado:** integridade de roteamento, autorização e enquadramento das
  requisições.
- **Superfície:** parser externo do gateway e parser interno do `sisterd`.
- **Cenário:** `Content-Length`, `Transfer-Encoding`, whitespace, Host ou método
  recebem interpretações diferentes e permitem smuggling ou desvio de política.
- **Controles definidos:** HAProxy em modo HTTP estrito; HTTP/1.1 único; CL
  duplicado, TE, CL+TE e whitespace ambíguo rejeitados; Host e métodos em
  allowlist.
- **Testes definidos:** matriz diferencial de framing, Host, método e protocolo
  em SEC-03V; mutações inseguras do perfil já falham no pipeline.
- **Evidências:** ADR-0020, `docs/security/GATEWAY_SECURITY_PROFILE.md` e
  `ops/gateway/security-profile.json`; evidência de processo pendente SEC-03V.
- **Risco residual:** nenhum controle externo está implantado ou comparado ao
  parser do `sisterd`.
- **Owner:** manutenção do gateway e transporte do `sisterd`.
- **Estado:** `PROFILE_DEFINED`.

### TH-HTTP-03 — Exaustão de recursos HTTP

- **Ativo afetado:** workers, memória, conexões, descritores e disponibilidade.
- **Superfície:** conexões HTTP, corpos, fila de jobs e login.
- **Cenário:** corpo grande, requisição lenta ou cardinalidade de chaves esgota
  recursos.
- **Controles:** tamanho máximo de corpo, fila e workers limitados, timeouts de
  socket, buckets limitados, expiração e LRU; SEC-03A define limites de borda,
  deadlines absolutos, conexões e taxas multidimensionais.
- **Testes:** `tests/security_hardening_tests.cpp` e
  `tests/sisterd_http_hardening_test.py`; perfil em
  `tests/gateway_security_profile_test.py`.
- **Evidências:** ADR-0019, `docs/evidence/security/SEC-01C-01D.md`, ADR-0020 e
  perfil SEC-03A; carga externa permanece pendente SEC-03V.
- **Risco residual:** timeouts de socket não contêm Slowloris integralmente;
  deadlines absolutos e quotas de borda pertencem ao SEC-03; o mecanismo de
  taxa mínima permanece explicitamente não comprovado para SEC-03B.
- **Owner:** manutenção do `sisterd`; operação do gateway para o residual.
- **Estado:** `PARTIALLY_CONTROLLED`.

### TH-HTTP-04 — Headers externos tratados como autoridade

- **Ativo afetado:** identidade, origem observada e correlação de auditoria.
- **Superfície:** headers recebidos pelo gateway e encaminhados ao `sisterd`.
- **Cenário:** cliente escolhe `X-Sister-*`, `Forwarded`, `X-Forwarded-*` ou
  `X-Request-ID` e influencia autorização, contenção ou logs.
- **Controles definidos:** remover todas as ocorrências externas, reconstruir
  somente origem, host, protocolo e ID autorizados, e manter `X-Sister-*` sem
  reconstrução.
- **Testes definidos:** matriz de headers forjados e correlação ponta a ponta;
  perfil rejeita qualquer confiança em valor fornecido pelo cliente.
- **Evidências:** ADR-0020 e perfil SEC-03A; evidência de processo pendente
  SEC-03V.
- **Risco residual:** o isolamento do upstream e a confiança condicionada ainda
  não foram implementados; o `sisterd` continua gerando seu próprio ID.
- **Owner:** manutenção do gateway e do `sisterd`.
- **Estado:** `PROFILE_DEFINED`.

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
- **Evidências:** `docs/evidence/security/SEC-02V.md` e
  `docs/evidence/security/SEC-02M.md`.
- **Risco residual:** cache de `jti` é local e perdido no reinício; distribuição
  e rotação de chaves continuam operacionais.
- **Owner:** manutenção de identidade do `sisterd` e manutenção do Nexo.
- **Estado:** `PARTIALLY_CONTROLLED` em `v0.2.7`. Aprovado somente para leitura
  interna e shadow; `v0.2.6` permanece inalterada.

### TH-WS-01 — Retenção de recursos por WebSocket

- **Ativo afetado:** workers, conexões e disponibilidade do plano de controle.
- **Superfície:** proxy WebSocket legado.
- **Cenário:** conexão persistente ocupa worker ou permanece sem limites
  adequados.
- **Controles:** proxy proibido com falha fechada em produção e permitido apenas
  por habilitação explícita no laboratório; SEC-03A nega todo `Upgrade` e
  WebSocket na borda.
- **Testes:** `tests/sisterd_transport_quarantine_test.py` e perfil mutado em
  `tests/gateway_security_profile_test.py`; handshake real pendente SEC-03V.
- **Evidências:** ADR-0015, baseline `v0.2.5`, ADR-0020 e perfil SEC-03A.
- **Risco residual:** código legado ainda existe para caracterização em
  laboratório; WebSocket definitivo, quotas e prazos pertencem ao SEC-03.
- **Owner:** arquitetura de transporte e operação do gateway.
- **Estado:** `PARTIALLY_CONTROLLED`.

### TH-PROXY-01 — Destino upstream controlável

- **Ativo afetado:** serviços locais, metadados e fronteiras entre subsistemas.
- **Superfície:** seleção do backend pelo gateway.
- **Cenário:** Host, caminho, header ou resolução fornecida pelo cliente altera
  o destino e transforma a borda em proxy aberto ou SSRF.
- **Controles definidos:** único servidor literal `127.0.0.1:8000`, sem
  descoberta dinâmica, `set-dst`, resolver ou acesso direto ao Nexo.
- **Testes definidos:** manipulação de Host, caminho, headers e destino, além de
  tentativa de acesso direto ao upstream.
- **Evidências:** ADR-0020 e perfil SEC-03A; isolamento real pendente SEC-03B/V.
- **Risco residual:** regra de host/cgroup ainda não implantada.
- **Owner:** operação de plataforma e manutenção do gateway.
- **Estado:** `PROFILE_DEFINED`.

### TH-PROXY-02 — Upstream retém ou devolve recursos sem limite

- **Ativo afetado:** conexões, memória e disponibilidade da borda.
- **Superfície:** fila, conexão, resposta e falha do `sisterd`.
- **Cenário:** upstream lento, indisponível ou excessivo retém recursos ou
  produz resposta sem limite.
- **Controles definidos:** prazos de fila, conexão e resposta; alvo de limite de
  16 MiB; destino único; falha externa fechada.
- **Testes definidos:** upstream lento, ausente, fila saturada e resposta grande.
- **Evidências:** ADR-0020 e perfil SEC-03A; execução pendente SEC-03V.
- **Risco residual:** o mecanismo simples para interromper resposta em 16 MiB
  ainda não foi comprovado; alta disponibilidade e streaming não pertencem à
  primeira baseline.
- **Owner:** manutenção do gateway e do `sisterd`.
- **Estado:** `PROFILE_DEFINED`.

### TH-AUD-01 — Correlação forjada ou log com segredo

- **Ativo afetado:** evidência operacional, credenciais e material criptográfico.
- **Superfície:** access log, métricas e `request_id` entre componentes.
- **Cenário:** cliente escolhe o ID, campos sensíveis aparecem em logs ou eventos
  não podem ser correlacionados.
- **Controles definidos:** ID hexadecimal novo na borda, campos estruturados,
  lista explícita de campos proibidos e métricas por regra de bloqueio.
- **Testes definidos:** busca por cookie, autorização, corpo, query, asserção e
  chave; correlação gateway–`sisterd`–Nexo–PostgreSQL.
- **Evidências:** ADR-0020 e perfil SEC-03A; retenção, integridade e execução
  pendentes SEC-03V.
- **Risco residual:** o ID único ainda não atravessa o processo real e os logs
  não possuem política operacional de retenção.
- **Owner:** operação de observabilidade e manutenção dos serviços.
- **Estado:** `PROFILE_DEFINED`.

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
| Concluído na baseline | `SEC-02M` — flag própria e política exata em `v0.2.7` |
| Backlog bloqueante antes de escrita | `SEC-02R` — replay persistente ou garantia transacional equivalente |
| Concluído como perfil, não implantado | `SEC-03A` — ADR-0020 e perfil executável |
| Pronto | `SEC-03B` — gateway mínimo em laboratório |
| Backlog imediato | `SEC-03C` — contenção de abuso na borda |
| Validação | `SEC-03V` — matriz negativa e evidência de processo |
| Backlog seguinte | `FED-01` — registro persistente de sistemas |

Perda de controle, validade ou evidência pode regredir maturidade, suspender a
capacidade ou bloquear a integração.

## Decisão de risco da baseline

A Coordenação do Projeto SisTer aprova os owners e estados acima para a
`v0.2.7`, com aceitação restrita dos seguintes riscos residuais:

- Slowloris, deadlines absolutos e quotas de borda permanecem em
  `TH-HTTP-03`, desde que o `sisterd` continue restrito a loopback e sem papel de
  servidor HTTP público até SEC-03V. SEC-03A define o controle, mas não reduz
  esse risco sem implantação e teste.
- A contenção de login usa o endereço diretamente observado; nenhuma confiança
  em origem encaminhada existe antes do gateway governado.
- O proxy WebSocket legado permanece fisicamente presente apenas para
  laboratório, desabilitado e proibido em produção.
- A ausência de execução do UBSan limita a evidência sobre comportamento
  indefinido e deve ser sanada antes de gate que exija essa cobertura; não é
  ocultada nem classificada como falha funcional.
- O cache de replay do Nexo não sobrevive a reinício. Isso é aceito somente
  porque a política publicada é idempotente e read-only; SEC-02R é obrigatório
  antes de qualquer escrita.

A aceitação não autoriza outra rota, capacidade de escrita, integração Compras,
exposição externa ou uso do `sisterd` como servidor HTTP público. SEC-02M
garante que tais pedidos falham antes da emissão e da conexão upstream. Esta
aprovação publica uma baseline interna de controles; não declara prontidão para
produção externa. Da mesma forma, `PROFILE_DEFINED` em SEC-03A não equivale a
`CONTROLLED_BASELINE`: somente SEC-03B/C/V podem sustentar essa transição.
