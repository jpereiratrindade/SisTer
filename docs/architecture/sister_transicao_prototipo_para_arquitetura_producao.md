# SisTer — Plano de Transição do Protótipo Integrado para uma Arquitetura de Produção

**Documento de arquitetura, engenharia de sistemas, segurança, governança e execução**
**Projeto:** SisTer — Sistema Inteligente e Resiliência de SSE
**Escopo inicial de validação:** `sisterd`, `sisterctl`, Sister-Clima e SisTer Nexo
**Status do documento:** proposta para decisão arquitetural e execução controlada
**Data de referência:** 31 de julho de 2026

---

## Atualização executável — baseline `v0.2.5`

Este plano preserva o diagnóstico do protótipo como contexto histórico. Desde a
sua redação, a baseline de segurança avançou sem concluir a arquitetura de
produção:

| Pacote | Estado na `v0.2.5` |
|---|---|
| SEC-00 — quarentena do transporte | concluído: loopback obrigatório e proxies legados proibidos em produção |
| SEC-01 — autorização por capacidades | concluído: políticas explícitas, negação por padrão e log correlacionado |
| SEC-01A — remoção do RBAC residual | concluído: papel não autoriza diretamente rotas sensíveis |
| SEC-01B — bootstrap offline | concluído: caminho absoluto, uso único e nenhuma sessão emitida |
| SEC-02 — identidade interna assinada | pendente e próximo pacote de segurança |

O código legado continua presente somente para laboratório e não é um fallback
de produção. Gateway especializado, identidade interna assinada, retirada física
dos proxies, eliminação do cookie interno e gates operacionais permanecem
pendentes. A referência canônica do estado atual é a
[baseline de segurança do `sisterd`](./SISTERD_SECURITY_BASELINE.md).

---

## 1. Síntese executiva

A integração atual demonstrou que o SisTer consegue oferecer autenticação central, acesso unificado e encaminhamento protegido para subsistemas distintos. Esse resultado é relevante: o fluxo funcional foi validado e a inclusão do Sister-Clima tornou visíveis requisitos que não apareciam com a mesma intensidade nas integrações anteriores, sobretudo transporte WebSocket, conexões persistentes, propagação de identidade, consumo de recursos e dependência entre a disponibilidade do núcleo e a dos subsistemas.

Entretanto, a solução corrente ainda reúne no processo principal do `sisterd` responsabilidades demais: servidor HTTP, autenticação, gestão de usuários, arquivos estáticos, APIs administrativas, proxy reverso, túnel WebSocket, propagação de identidade, catálogo de integrações e regras específicas de Clima e Nexo. O fluxo funciona, mas a arquitetura ainda não deve ser classificada como concluída, sustentável ou pronta para produção.

A transição proposta não consiste em descartar o que foi feito. Consiste em:

1. **congelar e documentar o estado atual como referência funcional de desenvolvimento**;
2. **definir um contrato obrigatório e versionado para subsistemas**;
3. **separar transporte, identidade, autorização, domínio e adaptação**;
4. **substituir o repasse de cookie por identidade interna assinada e de curta duração**;
5. **migrar usuários e sessões para persistência transacional no PostgreSQL**;
6. **retirar do `main.cpp` o conhecimento específico de cada integração**;
7. **adotar gateway/proxy apropriado para HTTP, WebSocket, limites e observabilidade de transporte**;
8. **fazer Clima e Nexo conformarem ao mesmo contrato por meio de adaptadores**;
9. **criar testes de conformidade executáveis por qualquer subsistema presente ou futuro**;
10. **promover a solução por gates objetivos: desenvolvimento, integração, pré-produção e produção**.

A decisão arquitetural central é:

> **O SisTer governa a integração; o gateway protege e transporta; os adaptadores traduzem; os subsistemas preservam seus domínios.**

---

## 1.1 Estratégia de maturidade: Alfa, Beta, Gama e Produção

A transição será comunicada à equipe por três marcos de maturidade — **Alfa, Beta e Gama** — sem substituir as fases técnicas, os pacotes de trabalho ou o versionamento semântico. Esses marcos funcionam como **gates de engenharia**: uma versão somente muda de estágio quando satisfaz critérios objetivos de saída.

A nomenclatura será usada da seguinte forma:

- **Protótipo atual / pré-Alfa:** referência funcional congelada; demonstra o fluxo, mas conserva mecanismos provisórios.
- **Alfa:** consolida fundações arquiteturais, identidade, sessões e contrato comum em ambiente interno.
- **Beta:** integra Clima e Nexo pela arquitetura nova, com gateway, adaptadores, capacidades e registry.
- **Gama:** candidata à produção, submetida a hardening, observabilidade, carga, segurança, recuperação e operação assistida.
- **Produção 1.0.0:** promoção posterior à aprovação do gate Gama e retirada dos caminhos provisórios.

> **Alfa prova a arquitetura; Beta prova a integração; Gama prova a operação; Produção assume o compromisso.**

“Gama” é uma designação interna do SisTer. Como não é um estágio universalmente padronizado na indústria, toda comunicação externa deverá apresentá-la também como **candidata à produção** ou **pré-produção**. O versionamento dos artefatos continuará seguindo SemVer, por exemplo: `0.3.0-alpha.1`, `0.4.0-beta.1`, `0.9.0-gamma.1` e, após aprovação, `1.0.0`.

### Mapa executivo em uma página

| Estágio | Objetivo | Passos essenciais | Gate de saída |
|---|---|---|---|
| **Pré-Alfa — baseline** | Preservar o que funciona e impedir expansão do padrão provisório | congelar snapshot; registrar riscos; manter smoke tests; marcar integrações como provisórias; proibir novos proxies específicos | baseline reconstruível e verificável; limitações documentadas |
| **Alfa — fundações** | Provar a arquitetura sem depender do transporte definitivo | aprovar ADRs; criar `sister.subsystem/1.0.0`; modularizar o `sisterd` sem alterar comportamento; migrar usuários e sessões para PostgreSQL; criar capacidades; emitir identidade interna assinada; validar primeiro no Nexo em rota de laboratório | autenticação e revogação sobrevivem a reinícios; novo caminho não encaminha cookie; Nexo valida assinatura, audiência e capacidades; testes unitários e de contrato aprovados |
| **Beta — integração** | Provar Clima e Nexo no caminho arquitetural definitivo | escolher e implantar gateway; criar adaptadores conformantes; mover HTTP e WebSocket para o gateway; remover cabeçalhos forjáveis; eliminar cookie interno; filtrar interface por capacidades; ativar registry por manifestos; executar conformidade e rollback | Clima e Nexo passam na mesma suíte; `main.cpp` não contém proxy específico; WebSockets não bloqueiam o núcleo; rota anterior pode ser revertida de forma controlada |
| **Gama — pré-produção** | Provar que a solução pode ser operada com segurança e recuperação | observabilidade e auditoria; hardening e segredos; carga e segurança; testes de falha e reinício; backup/restauração; rotação de chaves; runbooks; piloto controlado; revisão de prontidão | nenhum risco crítico aberto; riscos altos tratados ou formalmente aceitos; carga, recuperação e rollback comprovados; responsáveis e runbooks definidos; aprovações técnica, de segurança e de domínio |
| **Produção 1.0.0** | Assumir o compromisso operacional | promover artefatos assinados; remover mecanismos legados; monitorar implantação; registrar aceite; iniciar política regular de manutenção | operação estável dentro dos objetivos definidos; caminho provisório removido, não apenas desativado |

### Regra de promoção

Cada gate exige quatro evidências:

1. **artefato:** código, contrato, migração, configuração ou runbook versionado;
2. **teste:** execução automatizada ou ensaio operacional reproduzível;
3. **registro:** ADR, relatório, checklist ou evento de aprovação;
4. **responsável:** pessoa ou papel que aceita o resultado e assume sua manutenção.

A passagem de estágio não ocorrerá por data, percepção de progresso ou demonstração visual. Uma funcionalidade pode estar “funcionando” e ainda permanecer no estágio anterior caso faltem isolamento, segurança, testes, recuperação ou documentação.

### Relação com as fases técnicas

- **Pré-Alfa:** Fase 0.
- **Alfa:** Fases 1, 2 e 3.
- **Beta:** Fases 4, 5 e 6.
- **Gama:** Fase 7 e preparação da Fase 8.
- **Produção 1.0.0:** conclusão formal da Fase 8.

Essa agregação permite que a equipe enxergue início, meio e fim sem transformar um programa de engenharia em três blocos vagos.

---

## 2. Objetivo do documento

Este documento define o caminho necessário para retirar a integração atual da condição de protótipo e alcançar uma arquitetura que possa ser operada com segurança, auditabilidade, previsibilidade e capacidade de evolução.

Ele deve orientar:

- decisões da equipe de arquitetura;
- decomposição técnica do `sisterd`;
- evolução do Sister-Clima e do SisTer Nexo;
- criação de contratos comuns;
- segurança de identidade e credenciais;
- persistência de usuários e sessões;
- observabilidade e auditoria;
- testes de unidade, integração, contrato, segurança, carga e recuperação;
- implantação e operação com `systemd` ou infraestrutura equivalente;
- critérios objetivos para declarar a solução pronta para produção;
- integração de Studio, Compras, SisTer-Campo e subsistemas futuros.

---

## 3. Escopo

### 3.1 Incluído

- `sisterd` como autoridade de identidade, governança e controle de integração;
- `sisterctl` como ferramenta administrativa e de conformidade;
- Sister-Clima como primeiro caso com HTTP e WebSocket;
- SisTer Nexo como primeiro caso de integração HTTP e autorização por capacidades;
- PostgreSQL como persistência transacional;
- gateway/reverse proxy especializado;
- contrato comum de subsistema;
- identidade interna assinada;
- adaptadores de integração;
- registro de serviços e manifestos;
- observabilidade, auditoria e resiliência;
- operação local, institucional e futura evolução distribuída.

### 3.2 Não incluído nesta primeira transição

- reescrita completa dos domínios internos de Clima ou Nexo;
- unificação dos bancos de dados dos subsistemas;
- adoção obrigatória de uma única linguagem ou framework;
- implantação imediata em ambiente de alta disponibilidade multi-região;
- uso obrigatório de Kubernetes;
- substituição de todas as interfaces web;
- desenho completo de autorização de todos os subsistemas futuros.

Esses temas poderão evoluir posteriormente, sem bloquear a saída da fase de protótipo.

---

## 4. Estado atual observado

## 4.1 Capacidades já demonstradas

O `sisterd` atual demonstra, em um único processo:

- servidor HTTP próprio;
- leitura e validação defensiva de requisições;
- limites de cabeçalhos, corpo, destino e quantidade de cabeçalhos;
- timeouts de cliente e upstream;
- pool de threads e fila limitada;
- autenticação e cadastro inicial;
- gerenciamento administrativo de usuários;
- sessão por cookie `HttpOnly`, `SameSite=Strict` e opção `Secure`;
- limitação de tentativas de login;
- verificação de mesma origem para métodos inseguros;
- cabeçalhos de segurança;
- arquivos estáticos;
- APIs internas do SisTer;
- encaminhamento HTTP para Nexo e Clima;
- encaminhamento WebSocket para Clima;
- propagação de identidade por cabeçalhos;
- token compartilhado opcional entre proxy e subsistema;
- `request_id` e logs estruturados básicos;
- limites de resposta de proxy;
- uso de loopback para subsistemas privados;
- parada controlada por sinais.

O `sisterctl` demonstra:

- validação de manifestos;
- verificação e migração de banco por scripts;
- importação administrativa de usuários;
- entrada de senha sem eco no terminal;
- códigos de saída distintos para uso em automação.

Essas capacidades formam uma boa referência funcional. Elas não devem ser confundidas com o desenho final, mas também não devem ser perdidas durante a transição.

## 4.2 Responsabilidades acumuladas no `sisterd`

O processo principal passou a concentrar:

| Responsabilidade | Situação atual | Destino recomendado |
|---|---|---|
| Socket TCP e protocolo HTTP | Implementação própria | Gateway/biblioteca HTTP madura |
| TLS | Externo ou ausente no processo | Gateway |
| Arquivos estáticos | `sisterd` | Gateway ou serviço web dedicado |
| Autenticação | `sisterd` | Manter como domínio do SisTer |
| Sessões | arquivo/estrutura atual | PostgreSQL e repositório dedicado |
| Gestão de usuários | `sisterd` | Serviço/módulo de identidade do SisTer |
| Autorização | papéis e condicionais | Política por capacidades |
| Proxy HTTP | artesanal | Gateway especializado |
| Proxy WebSocket | túnel artesanal | Gateway especializado |
| Identidade interna | cabeçalhos + token | envelope assinado e de curta duração |
| Rotas de subsistemas | codificadas no `main.cpp` | registro orientado por manifestos |
| Saúde de subsistemas | parcial | contrato comum de health/readiness |
| Auditoria | logs básicos | eventos persistidos e correlacionados |
| Governança de contratos | parcial | registry versionado e validado |

## 4.3 Mecanismos que permanecem provisórios

Devem ser classificados formalmente como provisórios de desenvolvimento:

1. túnel WebSocket implementado no processo principal;
2. repasse do cookie de sessão ao Sister-Clima;
3. identidade em cabeçalhos sem prova criptográfica por requisição;
4. token interno compartilhado como proteção principal;
5. persistência de usuários e/ou sessões em arquivo;
6. portas e rotas específicas de Clima e Nexo no código;
7. autorização baseada predominantemente em `role`;
8. fallback estático de sistemas e contratos misturado ao runtime;
9. pool de threads compartilhado entre HTTP normal e conexões persistentes;
10. ausência de suíte comum de conformidade dos subsistemas.

## 4.4 Classificação atual recomendada

```yaml
system: sister
integration_stage: development_prototype
functional_flow_validated: true
production_ready: false
security_review_complete: false
contract_conformance_complete: false
load_validation_complete: false
recovery_validation_complete: false
```

Para os subsistemas:

```yaml
sister_clima:
  status: functionally_integrated_provisional
  websocket: artesanal
  browser_cookie_forwarded: true
  production_ready: false

sister_nexo:
  status: functionally_integrated_provisional
  transport: artesanal_http_proxy
  identity_contract: provisional_headers
  production_ready: false
```

---

## 5. Princípios arquiteturais obrigatórios

## 5.1 Segurança por padrão

- nenhum subsistema deve ser exposto diretamente à rede de usuários;
- credenciais externas terminam no gateway/SisTer;
- o cookie do navegador nunca atravessa a fronteira de um subsistema;
- todo acesso é negado por padrão;
- toda capacidade deve ser explicitamente concedida;
- segredos não devem ser versionados no repositório;
- comunicação interna deve ser autenticada;
- tokens devem ter audiência e expiração específicas;
- logs não devem registrar senhas, cookies ou tokens completos;
- configuração de produção deve falhar quando faltarem requisitos de segurança.

## 5.2 Autonomia de domínio

Cada subsistema mantém:

- modelo de domínio;
- banco de dados próprio quando necessário;
- linguagem e framework;
- regras científicas ou operacionais;
- ciclo de desenvolvimento;
- decisões internas que não rompam o contrato de integração.

## 5.3 Integração orientada por contratos

A integração não deve depender de condicionais específicas no núcleo. Todo subsistema deve declarar e implementar:

- identidade do sistema;
- versão;
- contrato suportado;
- capacidades;
- endpoints técnicos;
- requisitos de transporte;
- saúde;
- política mínima de auditoria;
- erros padronizados;
- dependências relevantes;
- forma de desativação segura.

## 5.4 Menor privilégio

Papéis institucionais são resolvidos em capacidades. O subsistema recebe apenas as capacidades necessárias para a operação atual.

## 5.5 Separação entre autenticação e autorização

- autenticação responde **quem é o sujeito**;
- autorização responde **o que o sujeito pode fazer neste contexto**;
- o gateway autentica;
- o SisTer decide a política;
- o subsistema verifica e aplica capacidades sobre seus recursos.

## 5.6 Observabilidade como parte do contrato

Nenhuma integração é considerada concluída sem:

- logs correlacionáveis;
- métricas mínimas;
- health check;
- readiness check;
- identificação da versão;
- rastreio de falhas de dependência;
- auditoria das operações relevantes.

## 5.7 Evolução incremental e reversível

A transição deve:

- preservar o fluxo atual enquanto o novo caminho é validado;
- permitir rollback;
- usar feature flags ou configuração de rota;
- evitar migração “tudo ou nada”;
- promover subsistemas individualmente.

---

## 6. Arquitetura-alvo

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Navegador / cliente autorizado                                     │
│ - HTTPS                                                             │
│ - cookie opaco do SisTer                                            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Gateway SisTer                                                      │
│ - TLS                                                               │
│ - HTTP/1.1, HTTP/2 e WebSocket                                      │
│ - limites de conexão e requisição                                   │
│ - timeouts e backpressure                                           │
│ - roteamento                                                        │
│ - chamada de autenticação/autorização                               │
│ - propagação de request/correlation id                              │
│ - métricas de transporte                                            │
└───────────────┬───────────────────────────────┬─────────────────────┘
                │                               │
                ▼                               ▼
┌─────────────────────────────┐    ┌──────────────────────────────────┐
│ Núcleo de controle SisTer   │    │ Conteúdo web / frontend          │
│ - identidade               │    │ - recursos estáticos             │
│ - sessões                  │    │ - interface orientada por        │
│ - usuários                 │    │   capacidades                     │
│ - capacidades              │    └──────────────────────────────────┘
│ - contratos                │
│ - registro de sistemas     │
│ - acordos de integração    │
│ - emissão de identidade    │
│ - auditoria                │
└───────────────┬─────────────┘
                │ identidade interna assinada
                │ contrato e capacidades
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Rede privada de subsistemas                                        │
│                                                                     │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│ │ Adapter SisTer   │  │ Adapter SisTer   │  │ Adapter SisTer   │    │
│ │ Sister-Clima     │  │ SisTer Nexo      │  │ Sister-Studio    │    │
│ └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘    │
│          ▼                     ▼                     ▼              │
│    domínio Clima         domínio Nexo          domínio Studio       │
└─────────────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PostgreSQL e armazenamento por domínio                             │
│ - identidade e sessões do SisTer                                   │
│ - auditoria do SisTer                                               │
│ - bancos exclusivos dos subsistemas quando aplicável               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Responsabilidades dos componentes

## 7.1 Gateway

Responsável por:

- terminação TLS;
- protocolo HTTP e WebSocket;
- limites de tamanho;
- limites de conexões simultâneas;
- timeout de handshake, cabeçalhos, corpo, upstream e inatividade;
- backpressure;
- buffering configurado por rota;
- roteamento por manifestos aprovados;
- normalização e remoção de cabeçalhos não confiáveis;
- geração ou preservação de `request_id`;
- chamada ao núcleo do SisTer para sessão e autorização;
- inclusão do envelope interno assinado;
- métricas de latência, erro e conexão;
- health checks de transporte;
- circuit breaker quando suportado.

O gateway não decide regras de domínio e não consulta diretamente tabelas internas dos subsistemas.

## 7.2 Núcleo `sisterd`

Responsável por:

- usuários e credenciais;
- sessão externa;
- perfis institucionais;
- capacidades;
- políticas contextuais;
- registro de subsistemas;
- contratos e acordos de integração;
- emissão de identidade interna;
- revogação;
- auditoria central;
- API administrativa;
- API de descoberta das funcionalidades disponíveis ao usuário;
- validação de conformidade e estado dos subsistemas;
- governança das versões ativadas.

O `sisterd` não deve manter um bloco de código específico para cada subsistema.

## 7.3 Adaptador SisTer de cada subsistema

Responsável por:

- validar identidade interna;
- validar emissor, audiência, assinatura e expiração;
- validar contrato e acordo;
- mapear capacidades para ações locais;
- normalizar respostas e erros;
- expor endpoints técnicos comuns;
- registrar eventos de auditoria;
- propagar correlação;
- proteger o domínio de detalhes de transporte e identidade externa;
- manter compatibilidade controlada entre versões.

## 7.4 Subsistema

Responsável por:

- regras de domínio;
- validação dos recursos do próprio domínio;
- persistência própria;
- consistência de dados;
- autorização final sobre o recurso;
- qualidade científica ou operacional;
- eventos e resultados do domínio;
- recuperação de suas dependências.

## 7.5 `sisterctl`

Deve evoluir para ferramenta oficial de:

- validação de manifestos;
- validação de contratos;
- verificação de banco;
- migrações controladas;
- importação e recuperação administrativa;
- inspeção de registro de subsistemas;
- teste de conformidade;
- emissão de diagnóstico sanitizado;
- verificação de chaves públicas;
- rotação assistida de chaves;
- teste de readiness;
- promoção e desativação controladas de versões.

---

## 8. Contrato comum de subsistema

## 8.1 Nome e versão inicial

```text
sister.subsystem/1.0.0
```

O contrato deve ser composto por artefatos independentes e versionados:

```text
contracts/subsystem/1.0.0/
├── manifest.schema.json
├── capabilities.schema.json
├── identity-claims.schema.json
├── health.schema.json
├── readiness.schema.json
├── error.schema.json
├── audit-event.schema.json
├── openapi.yaml
├── examples/
└── README.md
```

## 8.2 Manifesto mínimo

```json
{
  "$schema": "https://sister.local/contracts/subsystem/1.0.0/manifest.schema.json",
  "system_id": "sister_clima",
  "name": "Sister-Clima",
  "version": "1.2.0",
  "contract": "sister.subsystem/1.0.0",
  "adapter_version": "1.0.0",
  "mount_path": "/integrations/clima/",
  "audience": "sister_clima",
  "transport": {
    "http": true,
    "websocket": true,
    "internal_endpoint": "http://127.0.0.1:8501"
  },
  "technical_endpoints": {
    "manifest": "/_sister/manifest",
    "health": "/_sister/health",
    "readiness": "/_sister/ready",
    "capabilities": "/_sister/capabilities"
  },
  "capabilities": [
    "climate.dashboard.read",
    "climate.analysis.execute",
    "climate.dataset.export"
  ],
  "data_ownership": "exclusive",
  "audit_level": "domain_relevant_operations",
  "production_eligible": false
}
```

## 8.3 Regras do manifesto

- `system_id` é estável e não reutilizável;
- `version` segue versionamento semântico;
- `contract` identifica a versão exata do contrato comum;
- `audience` é obrigatória para identidade interna;
- `mount_path` não pode colidir com outro sistema;
- endpoint interno não pode ser fornecido pelo usuário final;
- somente manifestos aprovados podem ser ativados;
- o digest do manifesto aprovado deve ser persistido;
- mudança incompatível exige nova versão principal;
- alterações de endpoint ou capacidade exigem nova revisão e auditoria;
- o runtime não deve carregar manifestos arbitrários do diretório web.

## 8.4 Capacidades

Capacidades devem ser:

- explícitas;
- estáveis;
- orientadas a ação e recurso;
- independentes de nomes de perfis institucionais;
- documentadas;
- testáveis;
- negadas por padrão.

Formato recomendado:

```text
<domínio>.<recurso>.<ação>
```

Exemplos:

```text
climate.dashboard.read
climate.analysis.execute
climate.dataset.export
nexo.projects.read
nexo.research_activities.manage
nexo.evidence.review
studio.projects.open
purchases.needs.review
```

## 8.5 Endpoints técnicos obrigatórios

### Manifesto

```http
GET /_sister/manifest
```

### Saúde do processo

```http
GET /_sister/health
```

Indica se o processo está vivo e capaz de responder.

### Prontidão

```http
GET /_sister/ready
```

Indica se o subsistema pode receber tráfego útil.

### Capacidades

```http
GET /_sister/capabilities
```

Devolve capacidades implementadas pela versão em execução.

## 8.6 Resposta de prontidão

```json
{
  "status": "ready",
  "system_id": "sister_clima",
  "version": "1.2.0",
  "contract_version": "1.0.0",
  "manifest_digest": "sha256:...",
  "dependencies": {
    "database": "ready",
    "meteorological_provider": "degraded"
  },
  "degraded_capabilities": [
    "climate.analysis.execute"
  ]
}
```

A resposta pública ou administrativa deve ser sanitizada e não expor segredos, credenciais, endereços sensíveis ou detalhes internos desnecessários.

## 8.7 Erro padronizado

```json
{
  "type": "authorization_denied",
  "code": "SISTER-CAPABILITY-REQUIRED",
  "title": "Capacidade não concedida",
  "detail": "A operação solicitada não está disponível para este sujeito.",
  "required_capability": "climate.dataset.export",
  "request_id": "req-...",
  "correlation_id": "corr-..."
}
```

Erros não devem revelar:

- stack traces;
- consultas SQL;
- caminhos locais;
- tokens;
- cabeçalhos internos;
- segredos;
- detalhes de configuração.

---

## 9. Identidade interna

## 9.1 Regra principal

> O cookie de sessão pertence ao navegador e ao SisTer. Ele nunca deve ser encaminhado para Clima, Nexo, Studio, Compras ou qualquer outro subsistema.

## 9.2 Fluxo proposto

1. navegador envia cookie opaco ao gateway;
2. gateway encaminha a validação da sessão ao `sisterd`;
3. `sisterd` consulta a sessão no PostgreSQL;
4. `sisterd` resolve usuário, perfis, contexto e capacidades;
5. `sisterd` emite envelope interno assinado;
6. gateway remove cabeçalhos de identidade enviados pelo cliente;
7. gateway adiciona somente a identidade interna confiável;
8. adaptador do subsistema valida a assinatura e as alegações;
9. subsistema verifica a capacidade exigida para a operação;
10. evento relevante é auditado.

## 9.3 Alegações mínimas

```json
{
  "iss": "sisterd",
  "sub": "urn:sister:user:7f...",
  "aud": "sister_clima",
  "iat": 1785501060,
  "nbf": 1785501060,
  "exp": 1785501120,
  "jti": "01J...",
  "session_id": "sess_...",
  "request_id": "req_...",
  "correlation_id": "corr_...",
  "contract": "sister.subsystem/1.0.0",
  "agreement": "sister-clima.integration/1.0.0",
  "purpose": "institutional_research",
  "capabilities": [
    "climate.dashboard.read",
    "climate.analysis.execute"
  ]
}
```

## 9.4 Características obrigatórias

- assinatura assimétrica;
- chave privada apenas no emissor;
- chaves públicas distribuídas aos adaptadores;
- `aud` específica por subsistema;
- vida curta;
- `jti` único;
- `iat`, `nbf` e `exp` validados;
- tolerância de relógio pequena e configurada;
- algoritmo permitido explicitamente;
- rejeição de algoritmo inesperado;
- rotação de chaves com `kid`;
- ausência de senha, cookie e segredo compartilhado;
- minimização de dados pessoais;
- nenhuma confiança em cabeçalhos equivalentes vindos do cliente.

## 9.5 Cabeçalhos internos recomendados

Há duas abordagens aceitáveis:

### Opção preferencial: token compacto assinado

```http
Authorization: Sister-Internal <token-assinado>
X-Request-ID: ...
X-Correlation-ID: ...
```

### Opção alternativa: assinatura HTTP estruturada

A requisição e cabeçalhos selecionados são assinados. Essa opção oferece vínculo mais forte com método, caminho e corpo, mas aumenta a complexidade inicial.

A primeira versão pode adotar token assinado de curta duração, desde que a equipe registre a possibilidade de evolução para assinatura vinculada à requisição em operações de maior risco.

## 9.6 Identidade de serviço

Além da identidade do usuário, cada serviço deve possuir identidade própria. O subsistema precisa saber:

- que a chamada veio do gateway autorizado;
- que o envelope foi emitido pelo `sisterd`;
- que a audiência corresponde ao subsistema;
- que o contrato está ativo.

Em ambientes futuros, mTLS pode complementar a assinatura da identidade.

---

## 10. Sessões e usuários no PostgreSQL

## 10.1 Objetivo

Substituir o arquivo como persistência operacional normal por repositórios transacionais.

## 10.2 Modelo mínimo de dados

### Usuários

```sql
users(
  id uuid primary key,
  name text not null,
  email_normalized text unique not null,
  password_hash text not null,
  status text not null,
  created_at timestamptz not null,
  updated_at timestamptz not null,
  password_changed_at timestamptz,
  disabled_at timestamptz
)
```

### Perfis

```sql
roles(
  id uuid primary key,
  code text unique not null,
  name text not null,
  status text not null
)
```

### Vínculos

```sql
user_roles(
  user_id uuid not null,
  role_id uuid not null,
  scope_type text,
  scope_id text,
  valid_from timestamptz,
  valid_until timestamptz,
  primary key(user_id, role_id, scope_type, scope_id)
)
```

### Capacidades

```sql
capabilities(
  code text primary key,
  description text not null,
  status text not null
)
```

### Mapeamento de perfil

```sql
role_capabilities(
  role_id uuid not null,
  capability_code text not null,
  constraints jsonb not null default '{}',
  primary key(role_id, capability_code)
)
```

### Sessões

```sql
sessions(
  id uuid primary key,
  token_hash bytea unique not null,
  user_id uuid not null,
  created_at timestamptz not null,
  expires_at timestamptz not null,
  last_seen_at timestamptz,
  revoked_at timestamptz,
  revocation_reason text,
  metadata jsonb not null default '{}'
)
```

### Chaves de assinatura

```sql
signing_keys(
  kid text primary key,
  algorithm text not null,
  public_key text not null,
  private_key_reference text,
  status text not null,
  valid_from timestamptz not null,
  valid_until timestamptz
)
```

A chave privada não precisa estar armazenada diretamente no banco. O campo de referência pode apontar para arquivo protegido, credencial do `systemd`, HSM ou secret manager.

## 10.3 Token de sessão externo

O navegador recebe um token aleatório e opaco. O banco guarda somente o hash do token.

Requisitos:

- gerador criptograficamente seguro;
- entropia adequada;
- rotação após autenticação;
- revogação no logout;
- expiração absoluta;
- expiração por inatividade, se adotada;
- invalidação após alteração crítica de credenciais;
- proteção contra fixação de sessão;
- índice sobre hash e expiração;
- limpeza periódica de sessões expiradas.

## 10.4 Migração do arquivo

O arquivo atual deve ser tratado como fonte de migração, não como fonte concorrente permanente.

Fluxo:

1. interromper alterações administrativas durante a janela controlada;
2. validar o arquivo;
3. importar usuários em transação;
4. preservar identificadores válidos;
5. validar contagem e unicidade;
6. desativar escrita no arquivo;
7. manter backup criptografado e com acesso restrito pelo período definido;
8. remover o arquivo do caminho operacional;
9. testar login, atualização, revogação e recuperação;
10. registrar o resultado da migração.

## 10.5 Bootstrap administrativo

Na baseline `v0.2.5`, produção proíbe o bootstrap HTTP. A primeira conta
administrativa é criada localmente por `sisterctl auth bootstrap-admin`, com
`SISTER_AUTH_FILE` explícito e absoluto. O comando lê a senha sem eco, cria e
persiste somente o usuário, não emite sessão e recusa uma segunda tentativa.

Na evolução para armazenamento transacional, o bootstrap deve continuar a:

- estar aberto somente quando não existir administrador ativo;
- ser fechado de forma transacional após a criação;
- exigir execução local; um eventual token remoto de instalação exigirá outra
  decisão arquitetural;
- produzir evento de auditoria;
- não reabrir automaticamente após erro de banco;
- falhar de forma segura.

O backend em arquivo ainda exige operação local única: duas execuções exatamente
simultâneas não são serializadas entre processos. Bloqueio interprocesso ou
criação exclusiva é uma melhoria de robustez anterior à operação ampliada.

---

## 11. Autorização por capacidades

## 11.1 Separação entre perfil e capacidade

Perfis são conceitos institucionais:

```text
admin
coordenador_pesquisa
pesquisador
tecnico_campo
consulta
```

Capacidades são permissões operacionais:

```text
nexo.projects.read
nexo.projects.manage
climate.dashboard.read
climate.analysis.execute
purchases.needs.review
```

O `sisterd` resolve:

```text
sujeito + perfis + escopo + acordo + finalidade + estado → capacidades
```

O subsistema aplica:

```text
capacidade + operação + recurso → permitir ou negar
```

## 11.2 Regras

- negar quando a capacidade não estiver presente;
- não inferir capacidade a partir de nome ou e-mail;
- não usar `admin` como passe universal sem política explícita;
- permitir escopo por projeto, unidade, atividade ou território;
- registrar decisões relevantes;
- manter política versionada;
- testar matriz de permissões;
- diferenciar leitura, criação, alteração, aprovação, exportação e administração.

## 11.3 Interface orientada por capacidades

A interface deve consultar uma API como:

```http
GET /api/me/capabilities
```

Resposta:

```json
{
  "subject": "urn:sister:user:...",
  "capabilities": [
    "nexo.projects.read",
    "climate.dashboard.read"
  ],
  "systems": {
    "sister_nexo": {
      "visible": true,
      "entrypoint": "/integrations/nexo/"
    },
    "sister_clima": {
      "visible": true,
      "entrypoint": "/integrations/clima/"
    },
    "sister_studio": {
      "visible": false
    }
  }
}
```

A interface não deve mostrar operações indisponíveis. O backend, porém, deve sempre verificar novamente. Ocultar melhora a experiência; autorizar no servidor garante a segurança.

---

## 12. Gateway e transporte

## 12.1 Por que retirar o túnel do `sisterd`

Conexões WebSocket são persistentes e requerem tratamento especializado. No modelo atual, uma conexão pode ocupar um trabalhador do mesmo pool usado por autenticação e APIs. Isso permite que o comportamento de um subsistema degrade o núcleo.

O gateway deve suportar:

- upgrade WebSocket;
- ping/pong e inatividade;
- limites por origem, usuário e subsistema;
- número máximo de conexões;
- buffer e backpressure;
- encerramento gracioso;
- métricas de conexões ativas;
- limite de tamanho de frame ou mensagem quando possível;
- timeout de handshake;
- proteção contra cliente lento;
- circuit breaker e upstream indisponível;
- preservação de correlação.

## 12.2 Opções tecnológicas

São candidatos adequados, sujeitos a prova de conceito:

- Envoy;
- Nginx;
- HAProxy;
- Caddy.

O critério não deve ser popularidade, mas aderência aos requisitos:

- HTTP e WebSocket;
- autenticação externa ou subrequest;
- remoção/inclusão controlada de cabeçalhos;
- métricas;
- configuração declarativa;
- reload seguro;
- operação no Fedora/Silverblue e no ambiente institucional;
- integração com `systemd`;
- manutenção pela equipe.

## 12.3 Escolha recomendada para a primeira consolidação

Adotar um gateway maduro e simples de operar, com configuração declarativa versionada e validação automatizada. A equipe deve executar uma prova comparativa pequena, usando os mesmos testes de Clima e Nexo.

A decisão deve ser registrada em ADR e não embutida informalmente no código.

## 12.4 Regras de cabeçalhos

O gateway deve remover qualquer cabeçalho externo com prefixos reservados, por exemplo:

```text
X-Sister-*
Forwarded
X-Forwarded-*
```

Depois, deve reconstruir apenas os cabeçalhos confiáveis.

Nunca deve encaminhar:

- `Cookie` externo aos subsistemas;
- `Authorization` externo sem política explícita;
- cabeçalhos de identidade enviados pelo navegador;
- informações pessoais não necessárias.

## 12.5 Rotas

Rotas devem vir do registro aprovado, não de condicionais compiladas.

Exemplo conceitual:

```yaml
routes:
  - system_id: sister_clima
    public_path: /integrations/clima/
    upstream: http://127.0.0.1:8501
    websocket: true
    auth_required: true
    audience: sister_clima
    agreement: sister-clima.integration/1.0.0
```

A geração da configuração pode ser automatizada, mas a ativação deve validar:

- esquema;
- assinatura/digest;
- colisões;
- endpoint permitido;
- contrato suportado;
- estado do acordo;
- readiness.

---

## 13. Registro de subsistemas

## 13.1 Fonte de verdade

O registro deve ser persistido no PostgreSQL e referenciar manifestos versionados no repositório ou em registry controlado.

Campos recomendados:

- `system_id`;
- nome;
- versão ativa;
- versão candidata;
- contrato;
- digest do manifesto;
- endpoint interno;
- caminho público;
- audiência;
- transportes;
- estado operacional;
- estado do acordo;
- capacidades declaradas;
- data de aprovação;
- responsável;
- motivo de suspensão;
- instante da última verificação.

## 13.2 Estados

```text
discovered
registered
conformance_pending
validated
active
degraded
suspended
revoked
retired
```

## 13.3 Regras de ativação

Um subsistema somente pode ficar `active` se:

- manifesto válido;
- contrato suportado;
- digest aprovado;
- endpoint em rede permitida;
- readiness positivo;
- identidade interna validada;
- capacidades conhecidas;
- testes de conformidade aprovados;
- acordo de integração ativo;
- responsável definido;
- rollback disponível.

---

## 14. Adaptadores de Clima e Nexo

## 14.1 Estratégia

Clima e Nexo devem ser usados para validar o contrato comum, pois representam integrações distintas:

- Clima: interface interativa, HTTP, WebSocket, dependências externas e análises;
- Nexo: operações de governança, projetos, atividades, evidências e autorização granular.

## 14.2 Adaptador do Sister-Clima

Deve implementar:

- validação da identidade interna;
- remoção da dependência do cookie do SisTer;
- endpoint de manifesto;
- health e readiness;
- declaração de capacidades;
- autorização de acesso ao dashboard;
- autorização separada para execução, exportação e administração;
- correlação de requisições HTTP e sessões WebSocket;
- limites de conexão;
- mensagens de erro padronizadas;
- auditoria de análises e exportações;
- indicação de degradação de provedores meteorológicos;
- política de encerramento de conexões após revogação ou expiração.

### Identidade em WebSocket

A autenticação deve ocorrer no handshake pelo gateway. O subsistema recebe envelope interno de curta duração. Para conexões longas, deve existir política explícita:

- duração máxima;
- revalidação ou renovação controlada;
- encerramento após expiração;
- revogação administrativa;
- limite por usuário;
- limite global.

## 14.3 Adaptador do SisTer Nexo

Deve implementar:

- manifesto e endpoints técnicos;
- validação de identidade interna;
- capacidades por projeto, atividade e evidência;
- filtragem da interface por capacidades;
- autorização final no backend;
- erros padronizados;
- auditoria das alterações;
- integração com acordos Nexo–Compras;
- manutenção da propriedade exclusiva de seu banco;
- correlação entre requisições do SisTer e ações de domínio.

## 14.4 Regra de isolamento

O adaptador não deve se transformar em um segundo domínio. Ele traduz e protege a fronteira; as decisões científicas e operacionais continuam dentro do subsistema.

---

## 15. Decomposição recomendada do `sisterd`

O objetivo não é necessariamente criar vários processos imediatamente, mas separar módulos e contratos internos.

```text
apps/sisterd/
├── main.cpp
├── bootstrap/
│   ├── config.cpp
│   └── application.cpp
├── identity/
│   ├── user_service.cpp
│   ├── password_service.cpp
│   ├── session_service.cpp
│   └── repositories/
├── authorization/
│   ├── capability_service.cpp
│   ├── policy_engine.cpp
│   └── scope.cpp
├── contracts/
│   ├── registry.cpp
│   ├── validator.cpp
│   └── compatibility.cpp
├── integrations/
│   ├── registry.cpp
│   ├── agreement_service.cpp
│   ├── token_issuer.cpp
│   └── readiness_service.cpp
├── audit/
│   ├── audit_service.cpp
│   └── audit_repository.cpp
├── api/
│   ├── auth_routes.cpp
│   ├── admin_routes.cpp
│   ├── systems_routes.cpp
│   └── capabilities_routes.cpp
├── db/
│   ├── connection_pool.cpp
│   ├── migrations.cpp
│   └── transaction.cpp
└── observability/
    ├── logging.cpp
    ├── metrics.cpp
    └── tracing.cpp
```

O `main.cpp` deve ficar restrito a:

1. carregar configuração;
2. inicializar dependências;
3. validar invariantes;
4. iniciar servidor/API;
5. tratar sinais;
6. executar desligamento gracioso.

---

## 16. Configuração e segredos

## 16.1 Classificação

### Configuração não sensível

- portas;
- caminhos públicos;
- limites;
- timeouts;
- versões de contrato;
- identificadores de sistema;
- níveis de log.

### Segredos

- senha do banco;
- chave privada de assinatura;
- tokens de bootstrap;
- credenciais de provedores externos;
- certificados privados;
- chaves de API.

## 16.2 Regras

- segredos não entram em Git;
- `.env` não é mecanismo de produção por si só;
- arquivos de segredo devem ter permissões mínimas;
- preferir credenciais do `systemd`, secret manager ou mecanismo institucional;
- processos recebem somente os segredos necessários;
- rotação não deve exigir alteração de código;
- logs devem mascarar URLs de banco e tokens;
- configuração de produção deve validar `Secure`, TLS, origem e chaves;
- valores padrão inseguros não podem ser usados em produção.

## 16.3 Fail closed

Em produção, o serviço deve recusar inicialização quando:

- chave de assinatura estiver ausente;
- banco de sessões estiver indisponível;
- cookie seguro estiver desativado sem exceção registrada;
- origem confiável estiver vazia;
- manifesto ativo for inválido;
- endpoint interno apontar para rede não permitida;
- algoritmo de assinatura não for permitido;
- migração obrigatória não estiver aplicada.

---

## 17. Banco de dados e propriedade dos dados

## 17.1 Princípio

Cada domínio é autoridade sobre seus dados. Integração não implica acesso direto às tabelas de outro subsistema.

## 17.2 Regras

- `sisterd` não consulta tabelas internas do Nexo ou Clima;
- Nexo não consulta diretamente tabelas de autenticação do SisTer;
- Clima não valida cookie no banco central;
- dados atravessam fronteiras somente por APIs, eventos ou pacotes contratados;
- cada troca registra versão de contrato, finalidade e proveniência;
- dados sensíveis não atravessam por padrão;
- cache e réplicas devem ter propriedade e validade declaradas;
- migrações são isoladas por domínio;
- falha de um banco de subsistema não deve corromper o banco do SisTer.

## 17.3 Conexões e pool

O `sisterd` deve usar pool de conexões com:

- limite configurável;
- timeout de aquisição;
- transações explícitas;
- rollback automático em erro;
- prepared statements quando aplicável;
- métricas de uso;
- health check separado de readiness;
- proteção contra saturação.

Um mutex global de banco pode ser aceitável no protótipo, mas limita concorrência e deve ser substituído por abstração apropriada.

---

## 18. Observabilidade e auditoria

## 18.1 Logs operacionais

Formato estruturado, preferencialmente JSON ou `key=value` estável:

```json
{
  "timestamp": "2026-07-31T12:00:00Z",
  "level": "info",
  "service": "sisterd",
  "version": "0.3.0",
  "request_id": "req_...",
  "correlation_id": "corr_...",
  "route": "/api/me",
  "method": "GET",
  "status": 200,
  "duration_ms": 12,
  "subject_hash": "..."
}
```

Não registrar:

- senha;
- corpo de login;
- cookie;
- token interno completo;
- chave privada;
- URL de banco com credencial;
- dados pessoais desnecessários.

## 18.2 Métricas mínimas

### Gateway

- requisições por rota e status;
- latência;
- bytes;
- conexões ativas;
- conexões WebSocket;
- erros de upstream;
- timeout;
- rejeições por limite;
- circuit breaker.

### `sisterd`

- login bem-sucedido e falho;
- sessões ativas;
- revogações;
- decisões de autorização;
- emissão de identidade interna;
- erro de validação de contrato;
- subsistemas ativos/degradados;
- conexões de banco;
- duração de consultas críticas.

### Subsistemas

- operações por capacidade;
- falhas de dependência;
- estado de readiness;
- filas e tarefas;
- exportações;
- conexões persistentes.

## 18.3 Correlação

- `request_id`: identifica uma requisição;
- `correlation_id`: conecta operações relacionadas entre serviços;
- `session_id`: identifica sessão sem expor o token;
- `audit_event_id`: identifica evento de auditoria.

Todos os componentes devem preservar a correlação.

## 18.4 Auditoria

Evento mínimo:

```json
{
  "event_id": "audit_...",
  "occurred_at": "2026-07-31T12:00:00Z",
  "actor": "urn:sister:user:...",
  "service": "sister_nexo",
  "capability": "nexo.projects.manage",
  "action": "project.update",
  "resource": "urn:nexo:project:...",
  "result": "allowed",
  "request_id": "req_...",
  "correlation_id": "corr_...",
  "contract": "sister.subsystem/1.0.0",
  "agreement": "nexo-sister.integration/1.0.0"
}
```

A auditoria deve ter política de retenção, controle de acesso e integridade.

---

## 19. Resiliência e controle de recursos

## 19.1 Isolamento

- gateway separado do `sisterd`;
- subsistemas em processos/serviços distintos;
- limites de CPU e memória por serviço quando possível;
- pools separados para tarefas de longa duração;
- limites específicos para WebSocket;
- fila limitada;
- recusa controlada em saturação;
- nenhum fallback silencioso que simule dado operacional real.

## 19.2 Timeouts

Definir por categoria:

- conexão;
- cabeçalhos;
- corpo;
- consulta de sessão;
- emissão de token;
- upstream HTTP;
- handshake WebSocket;
- inatividade WebSocket;
- consulta de banco;
- tarefa científica longa.

Uma tarefa longa não deve manter uma requisição HTTP comum aberta indefinidamente. Deve usar job assíncrono interno, estado e consulta de resultado, quando aplicável.

## 19.3 Circuit breaker

Quando um subsistema falhar repetidamente:

- interromper novas tentativas por período curto;
- responder erro sanitizado;
- manter o núcleo funcional;
- registrar degradação;
- permitir recuperação automática controlada;
- disponibilizar ação administrativa de suspensão.

## 19.4 Reinício

Após reinício:

- sessões válidas permanecem, salvo política contrária;
- chaves ativas são recuperadas com segurança;
- rotas são regeneradas a partir do registry;
- subsistemas não prontos não recebem tráfego;
- migrações são verificadas;
- conexões WebSocket antigas são encerradas naturalmente;
- auditoria continua consistente;
- não ocorre reabertura indevida do bootstrap.

## 19.5 Desligamento gracioso

- parar de aceitar novas requisições;
- marcar readiness como false;
- concluir requisições em curso dentro de limite;
- fechar WebSockets com política conhecida;
- descarregar logs;
- encerrar pool de banco;
- registrar motivo e estado final.

---

## 20. Estratégia de testes

## 20.1 Pirâmide de testes

```text
Testes de unidade
        ↓
Testes de componente
        ↓
Testes de contrato
        ↓
Testes de integração
        ↓
Testes ponta a ponta
        ↓
Testes de carga, falha e segurança
```

## 20.2 Unidade

Cobrir:

- parsing de configuração;
- validação de manifesto;
- compatibilidade de versões;
- hashing e comparação segura;
- geração e revogação de sessão;
- resolução de capacidades;
- emissão e validação de identidade interna;
- expiração e audiência;
- normalização de e-mail;
- políticas de bootstrap;
- sanitização de logs;
- validação de erros.

## 20.3 Contrato

Criar suíte `sister-conformance` executável contra qualquer subsistema.

Testes mínimos:

- manifesto válido;
- `system_id` consistente;
- versão declarada;
- health e readiness;
- capacidades compatíveis;
- rejeição sem identidade;
- rejeição com assinatura inválida;
- rejeição com audiência errada;
- rejeição com token expirado;
- rejeição sem capacidade;
- aceitação com capacidade;
- correlação preservada;
- erro no formato esperado;
- ausência de vazamento de segredo;
- comportamento em degradação;
- compatibilidade WebSocket quando declarado.

## 20.4 Integração

Cenários:

- login → sessão → acesso ao Nexo;
- login → sessão → acesso ao Clima;
- WebSocket autenticado sem repasse de cookie;
- revogação de sessão;
- usuário desativado;
- alteração de perfil;
- capacidade removida durante nova requisição;
- subsistema indisponível;
- banco temporariamente indisponível;
- chave em rotação;
- manifesto suspenso;
- conflito de rota;
- reinício do gateway;
- reinício do `sisterd`;
- reinício do subsistema.

## 20.5 Segurança

- força bruta e rate limit;
- fixação de sessão;
- CSRF;
- origem inválida;
- cookie sem `Secure` em produção;
- cabeçalhos forjados;
- request smuggling;
- path traversal;
- CRLF injection;
- corpos e cabeçalhos excessivos;
- algoritmo de assinatura inesperado;
- `kid` desconhecido;
- replay de token;
- audiência errada;
- bypass de rota;
- acesso direto à porta privada;
- SSRF por manifesto;
- exposição de segredos em logs;
- escalada por papel/capacidade;
- acesso de interface oculto mas endpoint protegido;
- sessão após alteração de senha;
- token interno roubado e expirado.

## 20.6 Carga

Medir separadamente:

- login;
- consulta de sessão;
- APIs administrativas;
- proxy HTTP;
- conexões WebSocket;
- mistura de tráfego;
- saturação de banco;
- fila do gateway;
- recuperação após pico.

Critério central: conexões do Clima não podem impedir login, administração ou acesso ao Nexo.

## 20.7 Falhas e recuperação

Injetar:

- queda do PostgreSQL;
- latência elevada;
- perda de conexão com Clima;
- processo Nexo encerrado;
- disco cheio para logs;
- chave pública desatualizada;
- manifesto inválido;
- relógio fora de tolerância;
- resposta upstream acima do limite;
- encerramento abrupto de WebSocket.

## 20.8 Regressão do protótipo

Antes de cada promoção, preservar testes equivalentes ao fluxo já validado:

- autenticação;
- acesso a Clima;
- acesso a Nexo;
- administração de usuários;
- APIs principais;
- arquivos web;
- logs e códigos de status.

---

## 21. CI/CD e integridade da cadeia de construção

## 21.1 Pipeline mínimo

1. formatação e lint;
2. compilação com warnings elevados;
3. análise estática;
4. testes de unidade;
5. testes de contrato;
6. testes de integração com PostgreSQL isolado;
7. verificação de migrações;
8. geração de SBOM;
9. verificação de dependências;
10. scan de segredos;
11. build reprodutível quando possível;
12. assinatura dos artefatos;
13. publicação de digest;
14. testes de instalação;
15. aprovação para promoção.

## 21.2 Regras

- `main` protegido;
- revisão obrigatória;
- nenhum segredo em fixture real;
- migrações imutáveis após publicação;
- contratos versionados;
- breaking change detectada;
- artefatos identificados por digest;
- versão do binário exposta em health;
- rollback referenciado;
- release notes com risco e compatibilidade.

## 21.3 Sanitizers e compilação

Para C++:

- AddressSanitizer em pipeline apropriado;
- UndefinedBehaviorSanitizer;
- ThreadSanitizer em cenários de concorrência;
- warnings como erros no perfil de CI;
- testes de fuzzing para parsers críticos;
- revisão de uso de `std::system` no `sisterctl`;
- limites explícitos e tipos seguros.

---

## 22. Operação com `systemd`

## 22.1 Serviços separados

```text
sister-gateway.service
sisterd.service
sister-clima.service
sister-nexo.service
```

## 22.2 Dependências

- gateway pode iniciar antes, mas só roteia para serviços prontos;
- `sisterd` depende do PostgreSQL acessível;
- subsistemas não precisam depender do `sisterd` para iniciar, mas readiness de integração depende da confiança configurada;
- não usar dependências rígidas que provoquem cascata desnecessária.

## 22.3 Hardening

Avaliar por serviço:

```ini
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
```

A configuração deve ser testada, pois alguns subsistemas podem exigir exceções. Exceções precisam ser mínimas e documentadas.

## 22.4 Credenciais

Preferir mecanismos de credenciais do `systemd` ou arquivos protegidos fora do repositório. A unidade não deve conter senha literal em arquivo versionado.

## 22.5 Reinício

- política de restart diferenciada;
- limite de tentativas;
- atraso progressivo;
- alerta em loop de falha;
- readiness antes de receber tráfego;
- não mascarar erro de configuração com reinício infinito.

---

## 23. Fases de transição

As fases são orientadas por gates, não por datas arbitrárias. Uma fase termina quando seus critérios forem satisfeitos.

Para comunicação executiva, elas são agrupadas nos marcos definidos na Seção 1.1: Fase 0 como **Pré-Alfa**; Fases 1–3 como **Alfa**; Fases 4–6 como **Beta**; Fase 7 e preparação da Fase 8 como **Gama**; e conclusão da Fase 8 como **Produção 1.0.0**. Os nomes de maturidade não eliminam nenhum critério técnico descrito a seguir.

## Fase 0 — congelamento e referência funcional

### Objetivo

Preservar o protótipo como baseline verificável.

### Entregas

- tag/release do estado atual;
- manifesto dos arquivos de referência;
- script de verificação de integridade;
- testes smoke do fluxo atual;
- documento de limitações;
- classificação `development_provisional`;
- lista explícita dos mecanismos proibidos para novas integrações.

### Critério de conclusão

É possível reconstruir e executar o baseline e comprovar que permanece idêntico à referência.

## Fase 1 — contrato comum e ADRs

### Objetivo

Definir a fronteira antes de reimplementar.

### Entregas

- `sister.subsystem/1.0.0`;
- schemas;
- OpenAPI técnico;
- modelo de capacidades;
- modelo de erro;
- modelo de auditoria;
- ADRs iniciais;
- suíte de conformidade em versão mínima.

### Critério de conclusão

Clima e Nexo podem ser descritos pelo mesmo contrato sem incluir detalhes de domínio indevidos.

## Fase 2 — persistência de identidade e sessões

### Objetivo

Remover arquivo do caminho operacional normal.

### Entregas

- migrações PostgreSQL;
- repositórios de usuário, perfil, capacidade e sessão;
- token opaco com hash no banco;
- revogação;
- limpeza de sessões;
- migração de usuários;
- testes;
- `sisterctl` atualizado.

### Critério de conclusão

Autenticação, administração, reinício e revogação funcionam sem depender de arquivo de usuários.

## Fase 3 — identidade interna assinada

### Objetivo

Eliminar cookie e identidade não comprovada na fronteira interna.

### Entregas

- emissor no `sisterd`;
- par de chaves inicial;
- endpoint ou distribuição de chaves públicas;
- validação nos adaptadores;
- audiência específica;
- rotação;
- testes de replay, expiração e assinatura;
- remoção do repasse de cookie no novo caminho.

### Critério de conclusão

Clima e Nexo rejeitam chamadas sem identidade interna válida e funcionam sem receber o cookie do navegador.

## Fase 4 — gateway especializado

### Objetivo

Retirar transporte artesanal do núcleo.

### Entregas

- ADR de escolha;
- configuração declarativa;
- TLS;
- proxy HTTP;
- proxy WebSocket;
- auth request;
- remoção de cabeçalhos forjados;
- métricas;
- limites;
- testes de carga e falha;
- rollback para rota antiga em desenvolvimento.

### Critério de conclusão

O `sisterd` não executa túnel WebSocket e o fluxo de Clima permanece funcional.

## Fase 5 — adaptadores conformantes

### Objetivo

Tornar Clima e Nexo exemplos de referência.

### Entregas

- adaptador Clima;
- adaptador Nexo;
- endpoints técnicos;
- capacidades;
- erros;
- auditoria;
- conformidade completa;
- documentação para novos subsistemas.

### Critério de conclusão

Ambos passam na mesma suíte de conformidade.

## Fase 6 — registro e roteamento orientados por manifestos

### Objetivo

Remover conhecimento específico de subsistemas do código do núcleo.

### Entregas

- registry no PostgreSQL;
- ativação por manifesto aprovado;
- geração/validação de rotas;
- estados de serviço;
- suspensão e revogação;
- `sisterctl subsystem ...`;
- interface administrativa.

### Critério de conclusão

Adicionar um subsistema conformante não exige editar o `main.cpp` do `sisterd`.

## Fase 7 — observabilidade, segurança e resiliência completas

### Objetivo

Atender os gates de pré-produção.

### Entregas

- métricas;
- dashboards;
- alertas;
- auditoria persistente;
- testes de carga;
- testes de recuperação;
- hardening de serviços;
- backup e restauração;
- runbooks;
- threat model atualizado;
- revisão de segurança.

### Critério de conclusão

Falhas de Clima ou Nexo não derrubam autenticação, núcleo ou outros subsistemas; incidentes são detectáveis e recuperáveis.

## Fase 8 — promoção controlada

### Objetivo

Mover de pré-produção para produção.

### Entregas

- checklist de produção;
- aprovação técnica;
- aprovação de segurança;
- aceite do responsável pelo domínio;
- plano de rollback;
- release assinada;
- observação pós-implantação;
- encerramento formal do mecanismo provisório.

### Critério de conclusão

Todos os critérios da seção de Definition of Done estão aprovados e registrados.

---

## 24. Pacotes de trabalho

## WP-01 — Baseline do protótipo

**Resultado:** referência imutável e reconstruível.
**Dependências:** nenhuma.
**Entregas:** tag, checksums, testes smoke, inventário de riscos.
**Aceite:** `verify-identical` e build limpo.

## WP-02 — Contrato de subsistema

**Resultado:** padrão único para integrações.
**Dependências:** WP-01.
**Entregas:** schemas, OpenAPI, exemplos, versionamento.
**Aceite:** Clima e Nexo modelados sem exceção estrutural.

## WP-03 — Capacidades e política

**Resultado:** autorização independente de papéis locais.
**Dependências:** WP-02.
**Entregas:** catálogo inicial, mapeamentos, API do usuário.
**Aceite:** interface e backend usam capacidades.

## WP-04 — Persistência de identidade

**Resultado:** usuários e sessões transacionais.
**Dependências:** banco e migrações.
**Entregas:** tabelas, repositórios, migração, revogação.
**Aceite:** reinício sem perda e logout revoga sessão.

## WP-05 — Emissão de identidade interna

**Resultado:** fronteira sem cookie.
**Dependências:** WP-03 e WP-04.
**Entregas:** chaves, issuer, validator, rotação.
**Aceite:** audiência errada e token expirado são rejeitados.

## WP-06 — Gateway

**Resultado:** transporte especializado.
**Dependências:** WP-05.
**Entregas:** configuração, TLS, WebSocket, limites, métricas.
**Aceite:** carga WebSocket não bloqueia APIs do SisTer.

## WP-07 — Adaptador Clima

**Resultado:** primeira integração HTTP/WebSocket conformante.
**Dependências:** WP-02, WP-05 e WP-06.
**Aceite:** nenhuma dependência do cookie do SisTer.

## WP-08 — Adaptador Nexo

**Resultado:** primeira integração de governança conformante.
**Dependências:** WP-02, WP-03 e WP-05.
**Aceite:** matriz de capacidades testada.

## WP-09 — Registry

**Resultado:** integração orientada por manifesto.
**Dependências:** WP-02 e adaptadores.
**Aceite:** nova rota sem alteração do núcleo.

## WP-10 — Observabilidade e auditoria

**Resultado:** operação rastreável.
**Dependências:** transversal.
**Aceite:** uma operação é correlacionada do gateway ao subsistema.

## WP-11 — Segurança e resiliência

**Resultado:** gates de pré-produção.
**Dependências:** todos os anteriores.
**Aceite:** revisão de risco, carga e recuperação aprovadas.

## WP-12 — Documentação operacional

**Resultado:** sistema operável por equipe, não por memória individual.
**Dependências:** arquitetura estabilizada.
**Aceite:** runbooks testados por pessoa que não implementou o componente.

---

## 25. Backlog técnico inicial

### Épico A — reduzir o `main.cpp`

- extrair configuração;
- extrair logging;
- extrair rotas de autenticação;
- extrair rotas administrativas;
- extrair sessão;
- extrair registro de sistemas;
- remover proxy WebSocket;
- remover proxy HTTP específico;
- eliminar fallbacks de produção embutidos.

### Épico B — banco

- schema de usuários;
- schema de sessão;
- schema de capacidades;
- schema de registry;
- schema de auditoria;
- migrações;
- pool de conexões;
- transações;
- backup e restauração.

### Épico C — segurança

- hashing de senha revisado;
- token de sessão opaco;
- assinatura assimétrica;
- rotação de chaves;
- política de segredo;
- scan de segredos;
- proteção de bootstrap;
- ameaça e abuso.

### Épico D — gateway

- prova comparativa;
- ADR;
- configuração;
- TLS;
- WebSocket;
- limites;
- métricas;
- auth request;
- hardening.

### Épico E — contratos

- schemas;
- OpenAPI;
- exemplos;
- compatibilidade;
- suíte de conformidade;
- documentação de adaptador;
- validação no `sisterctl`.

### Épico F — Clima

- remover cookie;
- validar identidade;
- manifest/health/ready;
- capacidades;
- auditoria;
- limites WebSocket;
- testes de degradação.

### Épico G — Nexo

- validar identidade;
- capacidades por domínio;
- interface filtrada;
- backend protegido;
- auditoria;
- contrato com Compras.

### Épico H — operação

- unidades `systemd`;
- credenciais;
- logs;
- métricas;
- alertas;
- runbooks;
- testes de reinício;
- rollback.

---

## 26. Critérios de aceite por estágio

## 26.1 Desenvolvimento integrado

- fluxo funcional;
- testes de unidade básicos;
- sem segredo no repositório;
- serviços privados;
- riscos conhecidos documentados;
- status explicitamente provisório.

## 26.2 Candidato a pré-produção

- contrato comum implementado;
- sessões no PostgreSQL;
- cookie não atravessa fronteira;
- identidade interna assinada;
- gateway especializado;
- capacidades granulares;
- testes de conformidade;
- observabilidade mínima;
- auditoria persistente;
- testes de carga e falha;
- backup e restauração testados;
- hardening aplicado;
- rollback testado.

## 26.3 Produção

- revisão de arquitetura aprovada;
- revisão de segurança aprovada;
- threat model atualizado;
- nenhum risco crítico aberto;
- riscos altos com tratamento e aceite formal;
- testes completos aprovados;
- alertas e runbooks ativos;
- responsáveis operacionais definidos;
- contratos e acordos ativos;
- artefatos assinados;
- migrações verificadas;
- recuperação testada;
- capacidade conhecida;
- manutenção e rotação de chaves definidas;
- documentação atualizada.

---

## 27. Definition of Done de uma integração

Uma integração de subsistema somente está concluída quando:

### Arquitetura

- [ ] usa o contrato comum suportado;
- [ ] possui adaptador delimitado;
- [ ] não exige alteração específica no núcleo;
- [ ] mantém propriedade de domínio definida;
- [ ] possui ADRs relevantes.

### Segurança

- [ ] serviço não está exposto ao usuário;
- [ ] cookie externo não é encaminhado;
- [ ] identidade interna é assinada;
- [ ] audiência é validada;
- [ ] capacidades são verificadas;
- [ ] segredos estão isolados;
- [ ] logs estão sanitizados;
- [ ] threat model foi revisado.

### Contratos

- [ ] manifesto válido e aprovado;
- [ ] schemas versionados;
- [ ] capacidades documentadas;
- [ ] erros padronizados;
- [ ] compatibilidade declarada;
- [ ] acordo de integração ativo.

### Operação

- [ ] health e readiness;
- [ ] métricas;
- [ ] logs correlacionados;
- [ ] auditoria;
- [ ] limites de recursos;
- [ ] reinício e desligamento testados;
- [ ] runbook disponível;
- [ ] rollback disponível.

### Testes

- [ ] unidade;
- [ ] contrato;
- [ ] integração;
- [ ] ponta a ponta;
- [ ] segurança;
- [ ] carga;
- [ ] falha e recuperação;
- [ ] regressão.

### Documentação

- [ ] manifesto;
- [ ] OpenAPI;
- [ ] capacidades;
- [ ] dependências;
- [ ] riscos;
- [ ] operação;
- [ ] troubleshooting;
- [ ] versão e mudanças.

---

## 28. Registro de riscos

| ID | Risco | Impacto | Tratamento |
|---|---|---:|---|
| R-01 | WebSockets consumirem todos os trabalhadores | Alto | gateway especializado e limites separados |
| R-02 | Cookie capturado por subsistema comprometido | Crítico | eliminar repasse do cookie |
| R-03 | Cabeçalhos de identidade forjados | Crítico | remover cabeçalhos externos e assinar identidade |
| R-04 | Token compartilhado comprometer todos os subsistemas | Alto | chaves assimétricas e audiência específica |
| R-05 | Arquivo de usuários corrompido ou exposto | Alto | PostgreSQL transacional e migração controlada |
| R-06 | `main.cpp` crescer por integração | Alto | registry e adaptadores |
| R-07 | Papel `admin` ser interpretado de forma ampla | Alto | capacidades explícitas |
| R-08 | Falha de Clima derrubar o núcleo | Alto | isolamento, circuit breaker e readiness |
| R-09 | Fallback aparentar operação normal com dado estático | Médio/Alto | estado explícito de degradação e sem fallback enganoso |
| R-10 | Segredo em unit file ou Git | Crítico | credenciais isoladas e scan |
| R-11 | Migração de sessão causar bloqueio de usuários | Alto | coexistência controlada, teste e rollback |
| R-12 | Incompatibilidade de contrato | Alto | versionamento, suíte de conformidade e gates |
| R-13 | Falta de auditoria impedir investigação | Alto | evento persistente e correlação |
| R-14 | Dependência excessiva de uma pessoa | Alto | documentação e runbooks testados |
| R-15 | Registry permitir SSRF | Crítico | endpoints permitidos, validação e aprovação |
| R-16 | Chave privada exposta | Crítico | secret storage, permissões e rotação |
| R-17 | Token interno reutilizado | Alto | vida curta, `jti`, audiência e controles de replay conforme risco |
| R-18 | Interface esconder ação mas API permitir | Alto | autorização obrigatória no backend |
| R-19 | Banco central indisponível impedir todo acesso | Alto | alta confiabilidade, timeouts e comportamento fail closed controlado |
| R-20 | Logs conterem dados pessoais excessivos | Médio/Alto | minimização, mascaramento e revisão |

---

## 29. ADRs recomendados

Criar inicialmente:

```text
ADR-0001 — Papel do sisterd como plano de controle
ADR-0002 — Adoção do contrato sister.subsystem/1.0.0
ADR-0003 — Separação entre gateway e núcleo
ADR-0004 — Identidade interna assinada
ADR-0005 — Sessões persistidas no PostgreSQL
ADR-0006 — Autorização orientada por capacidades
ADR-0007 — Adaptador por subsistema
ADR-0008 — Registro orientado por manifestos
ADR-0009 — Política de propriedade de dados
ADR-0010 — Observabilidade e auditoria obrigatórias
ADR-0011 — Escolha do gateway
ADR-0012 — Estratégia de chaves e rotação
ADR-0013 — Política de WebSocket
ADR-0014 — Estados de integração e promoção
ADR-0015 — Quarentena de transporte do sisterd
ADR-0016 — Autorização por capacidades com negação por padrão
ADR-0017 — Bootstrap administrativo local em produção
```

Cada ADR deve registrar:

- contexto;
- decisão;
- alternativas;
- consequências positivas;
- consequências negativas;
- riscos;
- estado;
- data;
- responsáveis;
- critérios de revisão.

---

## 30. Estrutura recomendada do repositório

```text
SisTer/
├── apps/
│   ├── sisterd/
│   └── sisterctl/
├── core/
├── contracts/
│   ├── subsystem/
│   │   └── 1.0.0/
│   ├── identity/
│   ├── audit/
│   └── agreements/
├── adapters/
│   ├── clima-reference/
│   └── nexo-reference/
├── gateway/
│   ├── config/
│   ├── templates/
│   └── tests/
├── storage/
│   ├── migrations/
│   └── fixtures/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── conformance/
│   ├── security/
│   ├── load/
│   └── recovery/
├── deploy/
│   ├── systemd/
│   ├── local/
│   └── production/
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── runbooks/
│   ├── threat-model/
│   └── integration-guide/
└── scripts/
    ├── verify/
    ├── migration/
    └── release/
```

---

## 31. Evolução do `sisterctl`

Comandos recomendados:

```text
sisterctl contract validate <arquivo>
sisterctl contract compatibility <antigo> <novo>
sisterctl subsystem validate-manifest <arquivo>
sisterctl subsystem conformance <endpoint>
sisterctl subsystem register <manifesto>
sisterctl subsystem activate <system-id> <version>
sisterctl subsystem suspend <system-id> --reason <motivo>
sisterctl subsystem status [system-id]
sisterctl identity import-user ...
sisterctl identity revoke-session <session-id>
sisterctl keys list
sisterctl keys rotate
sisterctl db check
sisterctl db migrate
sisterctl audit verify --from ... --to ...
sisterctl diagnostics
```

## 31.1 Segurança do `sisterctl`

O uso atual de `std::system` para scripts deve ser revisto. Embora exista citação de argumentos, o caminho mais robusto é:

- executar processo sem shell quando possível;
- validar caminhos de migração;
- limitar diretórios permitidos;
- registrar digest da migração;
- exigir modo administrativo;
- evitar imprimir URL de banco;
- retornar códigos de saída documentados;
- oferecer `--json` para automação.

---

## 32. Runbooks obrigatórios

Criar e testar:

1. banco indisponível;
2. sessão não validada;
3. chave expirada;
4. rotação de chave;
5. Clima indisponível;
6. Nexo indisponível;
7. gateway não inicia;
8. conflito de rota;
9. manifesto inválido;
10. subsistema degradado;
11. fila/conexões saturadas;
12. revogação emergencial de subsistema;
13. restauração de backup;
14. rollback de release;
15. migração falhou;
16. suspeita de vazamento de segredo;
17. usuário administrador bloqueado;
18. auditoria interrompida;
19. disco cheio;
20. relógio do host incorreto.

Cada runbook deve conter:

- sintomas;
- impacto;
- diagnóstico;
- comandos permitidos;
- ações de contenção;
- recuperação;
- validação final;
- evidências a preservar;
- responsável por comunicação.

---

## 33. Plano de coexistência e rollback

## 33.1 Coexistência

Durante a migração, manter dois caminhos somente em desenvolvimento controlado:

```text
legacy_proxy: enabled_for_validation
contract_gateway: enabled_for_selected_users
```

Regras:

- nenhum usuário deve cair aleatoriamente em caminhos diferentes;
- seleção por configuração ou grupo de teste;
- logs identificam o caminho;
- resultados comparáveis;
- caminho novo não compartilha cookie com subsistema;
- prazo de retirada definido por gate, não por esquecimento.

## 33.2 Rollback

Cada promoção deve registrar:

- versão anterior;
- artefatos e digests;
- migrações reversíveis ou estratégia forward-only;
- configuração anterior do gateway;
- chave anterior ainda válida pelo período de transição;
- como desativar a rota nova;
- como comprovar retorno à condição estável.

## 33.3 Migrações de banco

Para mudanças não reversíveis:

- expandir schema primeiro;
- publicar código compatível com antigo e novo;
- migrar dados;
- verificar;
- mudar leitura/escrita;
- retirar campo antigo posteriormente.

---

## 34. Decisões que não devem ser adiadas

1. papel arquitetural definitivo do `sisterd`;
2. existência de gateway separado;
3. contrato comum de subsistema;
4. identidade interna assinada;
5. persistência de sessões no PostgreSQL;
6. autorização por capacidades;
7. uso de adaptadores;
8. remoção do cookie da rede interna;
9. estados formais de integração;
10. critérios de produção.

## 34.1 Decisões que podem permanecer abertas por curto período

- produto exato de gateway;
- formato exato do token assinado;
- biblioteca criptográfica;
- solução final de métricas;
- momento de introdução de mTLS;
- divisão do `sisterd` em um ou mais processos;
- solução futura de alta disponibilidade.

Essas escolhas devem ser decididas por prova de conceito e ADR, sem bloquear a definição da arquitetura.

---

## 35. Ordem de implementação recomendada

A sequência de menor risco é:

```text
1. baseline
2. contrato comum
3. capacidades
4. PostgreSQL para usuários/sessões
5. identidade interna assinada
6. adaptador Nexo em HTTP
7. gateway HTTP
8. adaptador Clima
9. gateway WebSocket
10. registry por manifestos
11. observabilidade, carga e recuperação
12. promoção
```

O Nexo pode validar primeiro o novo modelo de identidade em HTTP, reduzindo variáveis. Em seguida, o Clima valida WebSocket e conexões persistentes sobre a mesma identidade e contrato.

---

## 36. Primeira intervenção concreta recomendada

A próxima intervenção no código não deve adicionar mais um bloco de proxy. Deve criar a primeira “costura” arquitetural correta.

### Entrega 1

Criar `contracts/subsystem/1.0.0` e descrever Clima e Nexo.

### Entrega 2

Extrair do `main.cpp`:

- configuração;
- logging;
- sessão;
- autorização;
- registry conceitual.

Sem alterar ainda o comportamento externo.

### Entrega 3

Criar tabelas de usuário, sessão e capacidade no PostgreSQL.

### Entrega 4

Criar emissor e validador de identidade interna em um teste isolado.

### Entrega 5

Adaptar Nexo ao novo token em rota de laboratório.

### Entrega 6

Escolher e validar gateway com Nexo.

### Entrega 7

Adaptar Clima e remover o cookie do handshake.

Essa sequência produz ganhos verificáveis a cada passo e evita reescrita de alto risco.

---

## 37. Indicadores de progresso

A equipe deve acompanhar indicadores de arquitetura, não apenas quantidade de funcionalidades:

- percentual de sessões no PostgreSQL;
- número de subsistemas conformantes;
- número de rotas específicas ainda compiladas;
- número de integrações que recebem cookie externo;
- cobertura da suíte de conformidade;
- percentual de capacidades documentadas;
- taxa de decisões de autorização auditadas;
- latência de validação da sessão;
- conexões WebSocket simultâneas suportadas;
- falhas de um subsistema que afetam outros;
- tempo e sucesso de recuperação;
- riscos críticos e altos abertos;
- runbooks testados;
- versões com rollback comprovado.

O indicador decisivo é:

> **quantas integrações novas podem ser adicionadas sem modificar o núcleo do SisTer.**

---

## 38. Governança da transição

## 38.1 Papéis

### Responsável de arquitetura

- mantém princípios e ADRs;
- avalia compatibilidade;
- impede exceções silenciosas.

### Responsável de segurança

- threat model;
- identidade;
- segredos;
- revisão de riscos;
- aceite de controles.

### Responsável do `sisterd`

- identidade;
- sessões;
- capacidades;
- registry;
- auditoria.

### Responsável do gateway

- transporte;
- TLS;
- limites;
- observabilidade de borda.

### Responsável de cada subsistema

- adaptador;
- conformidade;
- regras de domínio;
- operação e dados.

### Responsável de qualidade

- estratégia de testes;
- gates;
- evidências de aceite;
- regressão.

## 38.2 Regra de exceção

Qualquer exceção ao contrato deve conter:

- motivo;
- risco;
- duração;
- responsável;
- plano de remoção;
- teste de contenção;
- aprovação;
- data de revisão.

Uma exceção sem prazo e responsável torna-se arquitetura por acidente.

---

## 39. Resultado esperado

Ao final da transição:

- o usuário autentica uma vez no SisTer;
- a sessão é transacional e revogável;
- o navegador se comunica apenas com o gateway;
- o gateway trata HTTP e WebSocket;
- o cookie nunca chega ao subsistema;
- o `sisterd` emite identidade interna assinada;
- cada subsistema recebe audiência e capacidades específicas;
- Clima e Nexo passam pela mesma suíte de conformidade;
- rotas são derivadas de manifestos aprovados;
- um novo subsistema não exige edição do núcleo;
- falha de um subsistema não derruba os demais;
- operações são observáveis e auditáveis;
- reinícios, falhas e rollback são testados;
- decisões e riscos estão documentados;
- a integração pode ser classificada honestamente como pronta para produção.

---

## 40. Conclusão

A inclusão do Sister-Clima revelou uma fronteira arquitetural decisiva. O túnel WebSocket, o encaminhamento de cookie e a identidade por cabeçalhos permitiram validar o fluxo, mas não devem ser multiplicados como padrão. O valor do protótipo está justamente em mostrar, com evidência concreta, o que precisa ser abstraído, isolado e contratado.

O SisTer não deve absorver os domínios dos subsistemas nem transformar o `sisterd` em um proxy universal escrito à mão. Também não deve exigir que cada subsistema reinvente autenticação, autorização e auditoria.

A solução sustentável é estabelecer uma fronteira comum:

> **Subsistemas autônomos, adaptadores conformantes, identidade assinada, capacidades explícitas, transporte especializado e governança central do SisTer.**

O fluxo atual deve permanecer como baseline de desenvolvimento até que o novo caminho atenda aos gates definidos. Depois disso, os mecanismos provisórios devem ser removidos, não apenas desativados e esquecidos.

A saída da fase de protótipo não será marcada pelo fato de “continuar funcionando”. Será marcada quando o sistema funcionar **com arquitetura sustentável, segurança por padrão, contratos verificáveis, isolamento de falhas, operação recuperável e evidências objetivas de conformidade**.

---

# Apêndice A — Checklist da reunião de decisão

- [ ] Confirmar papel do `sisterd` como plano de controle.
- [ ] Aprovar criação do gateway separado.
- [ ] Aprovar `sister.subsystem/1.0.0`.
- [ ] Aprovar adaptadores por subsistema.
- [ ] Aprovar PostgreSQL para sessões.
- [ ] Aprovar identidade interna assinada.
- [ ] Aprovar capacidades como unidade de autorização.
- [ ] Aprovar Clima e Nexo como referências de conformidade.
- [ ] Aprovar fases e gates.
- [ ] Designar responsáveis por arquitetura, segurança, gateway e subsistemas.
- [ ] Criar ADRs iniciais.
- [ ] Congelar baseline do protótipo.

# Apêndice B — Critérios para escolher o gateway

| Critério | Peso sugerido |
|---|---:|
| HTTP e WebSocket robustos | obrigatório |
| Integração com autenticação externa | obrigatório |
| Remoção/inclusão segura de cabeçalhos | obrigatório |
| Limites e timeouts granulares | obrigatório |
| Métricas | obrigatório |
| Reload sem interrupção relevante | alto |
| Configuração declarativa validável | alto |
| Facilidade operacional pela equipe | alto |
| Integração com `systemd` | alto |
| Suporte a circuit breaker | médio/alto |
| mTLS futuro | médio |
| Comunidade e manutenção | médio |
| Complexidade total | deve ser minimizada |

# Apêndice C — Política temporária para o protótipo

Enquanto o novo caminho não estiver pronto:

1. executar apenas em ambiente de desenvolvimento controlado;
2. manter subsistemas em loopback ou rede privada;
3. usar token interno forte e fora do Git;
4. restringir usuários de teste;
5. não usar dados sensíveis reais desnecessários;
6. monitorar conexões WebSocket;
7. limitar workers e conexões;
8. documentar que o cookie é encaminhado ao Clima;
9. não adicionar novos subsistemas por cópia do bloco atual;
10. manter backup do arquivo de autenticação;
11. validar permissões de arquivos;
12. registrar incidentes e anomalias;
13. remover o caminho provisório após a promoção.

# Apêndice D — Frases de síntese

### Estado atual

> O fluxo integrado foi validado; a arquitetura de produção ainda está em construção.

### Arquitetura-alvo

> O SisTer governa a integração; o gateway protege e transporta; os adaptadores traduzem; os subsistemas preservam seus domínios.

### Critério de saída do protótipo

> Uma integração só está concluída quando continua funcional sob contratos versionados, identidade segura, limites de recursos, falhas controladas, auditoria e testes de conformidade.
