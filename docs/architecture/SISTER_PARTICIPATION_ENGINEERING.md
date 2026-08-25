# SisTer — Engenharia da Arquitetura de Participação

**Versão:** 0.2.0  
**Data:** 2026-08-25  
**Status:** proposta técnica para consolidação arquitetural  
**Escopo:** SisTer / `sisterd`, `sister-infra`, SisTer Nexo, SisTer Praxis, SisTer Atmos, SisTer Memória, `sister-reflexa`, `sister-reference` e superfície Web.

---

## 0. Propósito

Este documento transforma a proposição constitutiva do SisTer em decisões verificáveis de engenharia.

Seu objetivo não é prescrever uma tecnologia única para todos os sistemas, nem converter o ecossistema em um framework homogêneo. O objetivo é definir **limites, responsabilidades, contratos e critérios de aceitação** que permitam compor sistemas autônomos sem perda de identidade, estado, história, autoridade ou responsabilidade.

A questão de engenharia que motivou esta revisão foi:

> **Por que um sistema de domínio deveria conhecer a forma pela qual suas capacidades são transportadas?**

A resposta adotada é:

> **O núcleo de um participante não deve depender do transporte. Capacidades e contratos definem semântica; transportes apenas materializam comunicação.**

A segunda questão foi:

> **Se o transporte não pertence ao domínio, todo tráfego deve passar por `sisterd`?**

A resposta adotada é:

> **Não. `sisterd` pode centralizar a superfície e funções de controle de uma realização sem se tornar caminho obrigatório de todas as relações entre participantes.**

---

# 1. Decisão arquitetural central

## 1.1 Formulação

A arquitetura de engenharia do SisTer deve obedecer à seguinte separação:

> **Infra sustenta e opera. HAProxy protege a borda. `sisterd` oferece a superfície e o plano de controle de uma realização. Participantes mantêm domínio, estado, autoridade e capacidades. Relações governam sua composição. Transportes materializam a comunicação sem definir a identidade dos participantes.**

Essa formulação substitui a interpretação anterior em que `sisterd` poderia ser entendido como um dispatcher universal obrigatório.

---

## 1.2 Consequências

1. HTTP não integra a definição constitutiva de participante.
2. Unix Domain Socket (UDS) não integra a definição constitutiva de participante.
3. Uma capability não é um endpoint.
4. Um participante pode oferecer múltiplos bindings sem alterar seu domínio.
5. `sisterd` pode servir Web/BFF, discovery e observação sem possuir a verdade dos participantes.
6. Relações entre participantes podem ser diretas quando contrato, topologia e política assim determinarem.
7. Nenhum participante deve depender de `sisterd` para preservar identidade, estado, história ou autoridade.
8. `sister-infra` governa execução e conectividade, não semântica.
9. Um catálogo global deve ser derivado e reconstruível.
10. A Web representa a realidade observada; não a cria.

---

# 2. Princípios de engenharia

## P1 — Núcleo independente

Nenhum núcleo de domínio deve depender de:

- HTTP;
- HAProxy;
- `sisterd`;
- frontend;
- mecanismo específico de IPC;
- banco ou estado pertencente a outro participante.

O núcleo pode depender de **ports/interfaces abstratas** necessárias ao domínio, mas não de uma implantação específica dessas interfaces.

---

## P2 — Capability é semântica, endpoint é binding

Exemplo:

```text
capability:
    nexo.projects.read
```

Bindings possíveis:

```text
HTTP:
    GET /api/v1/nexo/projects

CLI:
    sisterctl invoke sister_nexo nexo.projects.read

UDS:
    invoke(participant="sister_nexo",
           capability="nexo.projects.read",
           ...)
```

A troca de binding não pode alterar:

- significado da capability;
- schema semântico;
- autoridade;
- regras de autorização;
- responsabilidade;
- evidência produzida.

---

## P3 — Plano de controle e plano de participação são distintos

### Plano de controle / superfície

Responsabilidades candidatas de `sisterd`:

- Web/BFF;
- sessão humana;
- integração com autoridade de identidade;
- discovery;
- catálogo derivado;
- observação;
- visão de relações;
- ações originadas na superfície;
- adaptação de bindings quando necessário.

### Plano de participação

Responsabilidades:

- comunicação entre participantes;
- invocação de capabilities;
- composição governada por `Relation`;
- propagação de contexto;
- evidências e receipts;
- deadlines, falhas e cancelamentos.

O plano de participação **não precisa passar obrigatoriamente por `sisterd`**.

---

## P4 — Centralização operacional não transfere autoridade

Pode haver:

- gateway único;
- processo de superfície único;
- autoridade de identidade comum;
- serviço de discovery;
- observabilidade centralizada;
- catálogos derivados.

Nenhum desses mecanismos pode se tornar, por conveniência, fonte de verdade para estado ou política de domínio que pertence a outro participante.

---

## P5 — Transporte é propriedade da implantação/relação

O transporte apropriado depende do contexto.

Exemplos:

- UDS para processos locais;
- HTTP/TLS para participantes remotos;
- eventos para comunicação assíncrona;
- arquivos para intercâmbio documentado;
- CLI para operação humana;
- outro protocolo futuro quando necessário.

O SisTer padroniza **garantias e semântica**, não uma tecnologia universal de transporte.

---

# 3. Modelo arquitetural de referência

```text
                         EXTERNAL EDGE
                              |
                              v
                        +-----------+
                        |  HAProxy  |
                        +-----+-----+
                              |
                       human surface
                              |
                              v
                  +----------------------+
                  |       sisterd        |
                  |                      |
                  | Web / BFF            |
                  | session              |
                  | discovery            |
                  | derived catalog      |
                  | relation view        |
                  | observations         |
                  +----------+-----------+
                             |
                  surface-originated calls
                             |
             +---------------+---------------+
             |               |               |
             v               v               v
           Nexo            Praxis          Atmos
             |               |               |
             |               |               |
             +----- governed relations ------+
                    |                 |
                    v                 v
                 Memória           Reflexa


            LOCAL / REMOTE PARTICIPATION PLANE
       transport selected per relation / deployment


====================================================
                    sister-infra
 process | sockets | TLS | releases | data plane
====================================================
```

---

# 4. Modelo interno de um participante

Um participante deve tender à seguinte separação:

```text
                adapters
        +----------+----------+
        |          |          |
       HTTP       UDS        CLI
        |          |          |
        +----------+----------+
                   |
                   v
             Application
                   |
                   v
                Domain
                   |
                   v
              Persistence
```

Nenhum adaptador é constitutivo.

Um sistema pode operar com um ou vários adaptadores conforme o perfil de implantação.

---

# 5. Fronteira de participação

## 5.1 Participant Manifest

O manifesto de participante deve declarar sem depender de endpoints HTTP obrigatórios:

- `participant_id`;
- versão;
- identidade;
- ownership;
- capabilities;
- contratos;
- autoridades;
- estado exposto;
- readiness semanticamente relevante;
- tipos de relações aceitas;
- bindings disponíveis na implantação atual;
- provenance do manifesto.

O binding deve ser informação operacional, não identidade.

---

## 5.2 Capability Invocation

A invocação deve ser definida de modo independente do transporte.

Envelope mínimo candidato:

```text
protocol_version
request_id
participant_id
capability_id
relation_id?        # quando a chamada está vinculada a Relation
subject_assertion?  # quando há sujeito humano/técnico delegado
purpose?
contract_ref
arguments
deadline
```

Resposta:

```text
request_id
status
result | error
decision?
evidence?
receipt?
```

O envelope deve ser válido tanto para:

```text
sisterd -> Nexo
```

quanto para:

```text
Nexo -> Praxis
Praxis -> Reflexa
Atmos -> Memória
```

Nenhum campo deve pressupor a existência de `sisterd`.

---

# 6. Relation como objeto de primeira classe

Uma `Relation` deve registrar explicitamente:

```text
relation_id
participants
roles
contract_ref
offered_capabilities
requested_capabilities
authority_boundaries
compatibility
lifecycle
transport_bindings?
evidence
```

A `Relation` responde:

- quem pode falar com quem;
- com qual finalidade;
- usando qual contrato;
- sob qual autoridade;
- quais capabilities podem ser acionadas;
- quais evidências devem ser preservadas;
- qual binding é válido naquela implantação.

O transporte pode mudar sem invalidar a relação, desde que as garantias contratuais permaneçam.

---

# 7. `sisterd`: responsabilidade candidata

## 7.1 `sisterd` pode

- servir a superfície Web integrada;
- disponibilizar BFF/API da superfície;
- manter sessão humana;
- integrar uma autoridade de identidade explicitamente nomeada;
- descobrir participantes;
- validar/copiar manifests;
- construir catálogo derivado;
- observar health/readiness;
- apresentar relações;
- encaminhar chamadas originadas da superfície;
- adaptar HTTP externo a um binding local;
- fornecer ferramentas comuns de observabilidade.

## 7.2 `sisterd` não deve

- definir a identidade autoritativa do Nexo/Praxis/Atmos;
- armazenar como fonte única o estado de domínio dos participantes;
- decidir autorização de objetos pertencentes ao Nexo;
- incorporar lógica de domínio para reduzir chamadas;
- inventar capabilities;
- ser caminho obrigatório de toda relação;
- tornar-se requisito para identidade, estado ou história dos participantes;
- assumir que discovery equivale a autoridade.

---

# 8. `sister-infra`: responsabilidade candidata

`Sister-infra` governa mecanismos operacionais:

- instalação;
- processos;
- systemd;
- socket activation;
- UDS;
- portas quando necessárias;
- HAProxy;
- TLS;
- release;
- atualização;
- rollback;
- data plane;
- DEVELOPMENT/CANDIDATE/OPERATIONAL;
- health operacional de componentes;
- permissões e ownership de sockets.

`Sister-infra` não declara:

- capabilities;
- regras de projeto;
- autoridade científica;
- autorização de domínio;
- relações semânticas;
- estado autoritativo de participantes.

---

# 9. HAProxy

HAProxy permanece borda especializada.

Responsabilidades:

- TLS;
- SNI/hosts;
- limites;
- headers;
- timeouts;
- rate limiting quando aplicável;
- escolha de upstream;
- proteção da borda.

HAProxy não deve conhecer:

- projetos;
- roles;
- evidências;
- regras científicas;
- autorização de domínio.

No perfil integrado, a superfície humana pode convergir para:

```text
Browser -> HAProxy -> sisterd
```

Bindings externos de participantes só devem ser publicados quando houver necessidade explícita de implantação/relação.

Essa publicação não é uma simples opção de roteamento: ela amplia a fronteira
qualificada pela ADR-0020 e exige decisão arquitetural, threat model, controles,
testes negativos, observabilidade e rollback próprios antes de promoção.

---

# 10. Decisões de transporte

## 10.1 HTTP

HTTP é permitido como adapter.

Não é obrigatório.

Um adapter HTTP próprio pode ser útil para:

- standalone;
- laboratório;
- integração remota;
- interoperabilidade externa;
- debugging.

## 10.2 Unix Domain Socket

UDS é candidato preferencial para processos locais porque:

- remove exposição TCP desnecessária;
- permite ownership/mode;
- permite peer credentials;
- integra-se bem a systemd;
- simplifica topologia local.

UDS não substitui autorização.

## 10.3 Protocolo sobre UDS

Não congelar imediatamente `sister.transport.unix-json/1.0.0`.

Primeiro provar a propriedade arquitetural E3.

Comparar durante o piloto:

1. HTTP/1.1 sobre UDS;
2. JSON framed sobre UDS;
3. eventualmente JSON-RPC;
4. outros apenas se houver necessidade demonstrada.

O objetivo inicial é demonstrar substituição de transporte, não inventar um novo RPC universal.

---

# 11. Segurança e identidade

## 11.1 Identidades distintas

### Peer técnico

Exemplo:

```text
uid
gid
pid
participant/process identity
```

Pode ser parcialmente verificado por UDS/`SO_PEERCRED`.

### Subject

Exemplo:

```text
human user
service principal
delegated actor
```

É transportado como asserção verificável.

---

## 11.2 Subject assertion

Uma asserção deve poder conter, quando aplicável:

```text
issuer
subject_id
audience
issued_at
expires_at
request_id/nonce
integrity/signature
claims necessários
```

O participante nunca deve interpretar uma role externa como autorização final sobre seus objetos.

---

## 11.3 Regra

```text
identidade federada
       !=
autorização local
```

O Nexo continua decidindo acesso a:

- projetos;
- atividades;
- evidências;
- objetos;
- operações de seu domínio.

---

# 12. Modificações por sistema

## 12.1 SisTer / `sisterd`

### SIS-001 — P1 — DEVE
Formalizar `sisterd` como **superfície/plano de controle da realização**, não “Core” soberano nem barramento obrigatório.

**Aceite:** ADR com matriz explícita “pode/não pode”.

### SIS-002 — P1 — DEVE
Criar `sister.participant/2.x` transport-neutral.

**Aceite:** manifesto validável sem `host`, `port` ou `path`.

### SIS-003 — P1 — DEVE
Criar `sister.capability-invocation/1.x`.

**Aceite:** mesmo envelope utilizável em chamadas mediadas e diretas.

### SIS-004 — P1 — DEVE
Criar `sister.relation/1.x`.

**Aceite:** relação auditável sem inferir termos de código hardcoded.

### SIS-005 — P1 — DEVE
Transformar `sister_systems`/catálogo em visão derivada.

**Aceite:** apagar catálogo não apaga identidade; discovery recompõe a visão.

### SIS-006 — P2 — DEVE
Modularizar `sisterd`:

```text
ingress/
surface/
identity/
discovery/
catalog/
relations/
observation/
invocation/
transports/
legacy/
```

### SIS-007 — P2 — DEVE
Concentrar a superfície humana no `sisterd`.

**Aceite:** navegador de produção não depende de `:8015`, `:8093` etc.

### SIS-008 — P3 — RECOMENDADO
Criar `sisterctl` usando a mesma camada de aplicação da superfície.

---

## 12.2 sister-infra

### INF-000 — P0 — DEVE
Concluir `OPS-003` DEVELOPMENT isolado.

### INF-001 — P1 — DEVE
Criar perfil integrado em que a **superfície humana** chegue a `sisterd`.

Não tornar isso uma regra de que todo binding entre participantes passa por `sisterd`.

### INF-002 — P1 — DEVE
Materializar UDS para `sisterd` em perfil promovível.

### INF-003 — P2 — DEVE
Definir socket plane:

- nomes;
- ownership;
- permissions;
- lifecycle;
- activation;
- cleanup;
- localização por perfil.

### INF-004 — P2 — DEVE
Distinguir health da superfície de health de bindings explicitamente publicados.

### INF-005 — P2 — RECOMENDADO
Manifesto de release deve registrar:

```text
transport_plane
surface_binding
participant_bindings
socket_paths
contract_versions
```

### INF-006 — P2 — DEVE
Concluir `OPS-004` CANDIDATE e `OPS-005` snapshot/restore antes de migração operacional.

---

## 12.3 SisTer Nexo

### NEX-000 — P0 — DEVE
Eliminar credencial compartilhada de bootstrap.

### NEX-001 — P1 — DEVE
Separar `Application Services` de HTTP.

**Aceite:** projetos/atividades/evidências/autorização testáveis sem servidor.

### NEX-002 — P1 — DEVE
Extrair persistence adapters/DAOs.

### NEX-003 — P1 — DEVE
Mapear operações para capabilities semânticas.

Exemplos candidatos:

```text
nexo.projects.read
nexo.projects.create
nexo.activity.record
nexo.evidence.record
nexo.procurement.needs.read
nexo.procurement.needs.write
```

### NEX-004 — P2 — DEVE
Criar participation adapter local após prova em reference/Praxis.

### NEX-005 — P2 — DEVE
Preservar integralmente autorização local.

### NEX-006 — P2 — RECOMENDADO
Desacoplar serving da UI do backend de domínio.

### NEX-007 — P2 — DEVE
Corrigir provenance de `local-dev` versus identidade federada.

### NEX-008 — P3 — RECOMENDADO
Manter Ollama como adapter/capability opcional.

Estrutura candidata:

```text
include/nexo/domain/
include/nexo/application/
include/nexo/ports/

src/domain/
src/application/

adapters/postgres/
adapters/participation/
adapters/http/
adapters/ollama/

web/
```

---

## 12.4 SisTer Praxis

Praxis é o primeiro piloto real porque já separa core/runtime/http.

### PRX-001 — P1 — DEVE
Adicionar participation adapter sem alterar core/runtime.

### PRX-002 — P1 — DEVE
Tratar OpenAPI como binding, não fonte exclusiva da semântica.

### PRX-003 — P2 — DEVE
No perfil integrado local, permitir operação sem `sister-praxis-http`.

### PRX-004 — P2 — RECOMENDADO
Integrar eventual UI à superfície comum.

---

## 12.5 sister-reference

É o primeiro laboratório.

### REF-001 — P1 — DEVE
Criar participant v2 sem HTTP constitutivo.

### REF-002 — P1 — DEVE
Implementar segundo binding e comparar com HTTP legado.

### REF-003 — P1 — DEVE
Testar:

- unknown capability;
- schema inválido;
- payload excessivo;
- timeout;
- stale relation;
- subject inválido;
- falha de peer;
- evidence/receipt.

---

## 12.6 SisTer Atmos

### ATM-001 — P1 — DEVE
Preservar core científico livre de transporte.

### ATM-002 — P2 — RECOMENDADO
Adicionar participation adapter externo ao core.

### ATM-003 — P3 — EXPERIMENTAL
Usar Atmos como prova de participante que nunca precisou ter HTTP em seu núcleo.

---

## 12.7 SisTer Memória

### MEM-001 — P1 — DEVE
Preservar documentos/repositórios como fonte e SQLite como índice reconstruível.

### MEM-002 — P2 — RECOMENDADO
Separar search/index/provenance do Web serving.

### MEM-003 — P2 — RECOMENDADO
Expor capabilities documentais com provenance.

### MEM-004 — P3 — OPCIONAL
Manter Web standalone somente como adapter de implantação.

---

## 12.8 sister-reflexa

### RFX-001 — P2 — RECOMENDADO
Separar core/evaluator/database de HTTP/frontend.

### RFX-002 — P3 — RECOMENDADO
Definir capabilities de avaliação/reflexão.

### RFX-003 — P3 — DEVE antes da integração
Não tornar Reflexa passagem obrigatória de todo ciclo reflexivo.

---

# 13. Superfície Web

## WEB-001 — P1 — DEVE
No perfil integrado, frontend fala apenas com API da superfície.

## WEB-002 — P1 — DEVE
Exibir provenance:

```text
declared_by
observed_by
derived_by
```

## WEB-003 — P2 — DEVE
Representar participantes e relações; não módulos internos de um “superaplicativo SisTer”.

## WEB-004 — P3 — RECOMENDADO
Não criar microfrontend/plugin system antes de existir necessidade real.

---

# 14. Contratos transversais

| Contrato | Estado |
|---|---|
| `sister.subsystem/1.0.0` | congelar como legado |
| `sister.participant/2.x` | novo |
| `sister.capability-invocation/1.x` | novo |
| `sister.relation/1.x` | novo |
| `sister.transport.http/1.x` | binding |
| `sister.transport.unix/*` | experimental até E3 |

---

# 15. Experimentos arquiteturais

## E1 — Ausência do centro

Parar `sisterd`.

**PASS:** participantes preservam identity/state/history/authority.

---

## E2 — Reconstrução

Apagar catálogo derivado.

**PASS:** participantes + relações recompõem a visão.

---

## E3 — Substituição de transporte

Executar a mesma capability por dois bindings.

**PASS:** mesma semântica, decisão e responsabilidade.

---

## E4 — Relação direta

Executar Nexo -> Praxis sem DB compartilhado e sem exigir mediação de `sisterd`.

**PASS:** chamada governada por `Relation`, resultado atribuível e autoridade preservada.

---

## E5 — Responsabilidade

Reconstruir uma decisão composta.

**PASS:** é possível identificar:

- dado de origem;
- participante que avaliou;
- relação;
- autorização;
- execução;
- evidência.

---

# 16. Testes técnicos mínimos

| Teste | PASS |
|---|---|
| T1 unknown capability | fail closed |
| T2 deadline | timeout/cancel sem exaustão |
| T3 payload inválido | rejeitado antes do domínio |
| T4 peer não autorizado | não acessa binding |
| T5 subject assertion inválida | participante nega |
| T6 stale relation | participante/adapter nega |
| T7 transport equivalence | mesma semântica |
| T8 direct relation | não depende de `sisterd` |
| T9 catalog rebuild | visão recomposta |
| T10 center absence | autonomia preservada |

---

# 17. Estratégia de migração

## Fase 0 — Proteção operacional

- NEX-000;
- OPS-003;
- congelar baseline operacional.

## Fase 1 — Contratos

- participant v2;
- capability invocation;
- relation draft.

## Fase 2 — Reference

- segundo binding;
- testes negativos;
- E3.

## Fase 3 — Praxis

- participation adapter;
- equivalência sem alterar core/runtime.

## Fase 4 — Nexo application boundary

Pode ocorrer em paralelo com os pilotos:

- NEX-001;
- NEX-002;
- NEX-003.

Essas mudanças são valiosas mesmo que a decisão de transporte evolua.

## Fase 5 — `sisterd`

- superfície;
- control plane;
- derived catalog;
- relation view;
- invocation para ações da superfície.

## Fase 6 — Infra

- UDS;
- socket plane;
- perfil integrado;
- CANDIDATE;
- snapshot/restore.

## Fase 7 — Nexo transport

Somente depois de E3 PASS em reference/Praxis.

## Fase 8 — Demais sistemas

Adicionar adapters conforme relações concretas exigirem.

## Fase 9 — Web

Redesenhar sobre a realidade já materializada.

---

# 18. O que não fazer

1. Não mover lógica do Nexo para `sisterd`.
2. Não obrigar todas as relações a passar por `sisterd`.
3. Não transformar UDS em dogma.
4. Não inventar RPC próprio antes de provar necessidade.
5. Não expor `invoke(anything)` irrestrito ao navegador.
6. Não transformar Infra em fonte de capabilities.
7. Não transformar Memória em banco global soberano.
8. Não adicionar HTTP ao core Atmos.
9. Não tornar Reflexa requisito universal.
10. Não remover HTTP do Nexo antes da separação Application/Domain.
11. Não migrar schema e topologia operacional na mesma janela.
12. Não confundir single ingress com single intermediary.
13. Não confundir identity assertion com authorization.
14. Não renomear processos/repositórios antes de estabilizar seus papéis.

---

# 19. Prioridades consolidadas

## P0 — imediato

- NEX-000;
- INF-000 / OPS-003.

## P1 — fundação

- SIS-001..005;
- participant/invocation/relation;
- REF-001..003;
- PRX-001/002;
- NEX-001..003;
- WEB-001/002.

## P2 — materialização

- modularização de `sisterd`;
- socket plane;
- profile integrated;
- Nexo participation adapter;
- Praxis sem HTTP no perfil integrado;
- Memória/Atmos adapters quando necessário.

## P3 — expansão

- `sisterctl`;
- Reflexa integrada;
- UI extensível;
- novos transportes.

---

# 20. Critérios de consolidação

A arquitetura será considerada consolidada quando:

- nenhum core de domínio exigir HTTP;
- capability existir independentemente de endpoint;
- uma capability puder trocar binding sem mudar semântica;
- `sisterd` puder ser desligado sem apagar identidade/estado/autoridade;
- relações diretas puderem existir sem centro obrigatório;
- catálogo puder ser reconstruído;
- Nexo continuar sendo autoridade de autorização local;
- Infra não conhecer semântica de domínio;
- Web não fabricar topologia;
- DEVELOPMENT/CANDIDATE estiverem isolados;
- evidência permitir reconstruir responsabilidade de composições.

---

# 21. Decisão sobre Unix

Unix é inspiração estrutural, não template literal.

Princípios aproveitados:

- mecanismos pequenos;
- composição;
- separação de mecanismo e política;
- processos substituíveis;
- IPC explícito;
- ausência de interface privilegiada;
- fronteiras claras.

O SisTer adiciona exigências próprias:

- identidade;
- autoridade;
- provenance;
- responsabilidade;
- Relation;
- evidência;
- reflexividade;
- aprendizagem governada.

Portanto:

```text
Unix
  -> disciplina de separação e composição

Princípios constitutivos SisTer
  -> critérios normativos

Engenharia
  -> implementação verificável
```

---

# 22. Síntese

O objetivo não é eliminar servidores HTTP.

O objetivo é eliminar a hipótese de que **ser participante SisTer significa ser um servidor HTTP**.

O objetivo também não é transformar `sisterd` em barramento universal.

O papel de `sisterd` é fornecer **superfície e plano de controle** quando uma realização SisTer precisar deles.

Os participantes continuam capazes de existir e estabelecer relações fora desse centro.

A arquitetura resultante pode ser resumida assim:

> **Participantes afirmam e decidem. Relações compõem. Transportes conectam. `sisterd` observa e representa. Infra sustenta e opera.**

Essa formulação deve orientar as próximas decisões de código, contratos, testes e implantação.

---

# 23. Próxima missão recomendada

1. Registrar ADR desta separação: **control plane vs participation plane**.
2. Criar `sister.participant/2.x`.
3. Criar `sister.capability-invocation/1.x`.
4. Criar `sister.relation/1.x` mínimo.
5. Criar reference participant v2.
6. Provar E3 com dois bindings.
7. Aplicar o piloto ao Praxis.
8. Em paralelo, começar a separação Application/Domain do Nexo.
9. Só então escolher/promover o transporte local.
10. Depois convergir `sisterd` e `sister-infra`.

---

## Histórico

### v0.2.0 — 2026-08-25

- substitui a hipótese de `sisterd` como dispatcher universal por **plano de controle/superfície**;
- explicita **plano de participação independente do centro**;
- mantém capability transport-neutral;
- transforma UDS em escolha de implantação, não princípio;
- adia padronização de protocolo UDS até evidência experimental;
- permite relações diretas entre participantes;
- antecipa refatoração Application/Domain do Nexo;
- preserva `sister-infra` como infraestrutura operacional;
- mantém HAProxy como borda especializada.

### v0.1.0 — 2026-08-25

- primeira avaliação consolidada de engenharia;
- introduziu a separação domínio/transporte;
- propôs participant, invocation e Relation;
- propôs UDS e centralização do ingresso HTTP;
- utilizada como base exploratória para esta revisão.
