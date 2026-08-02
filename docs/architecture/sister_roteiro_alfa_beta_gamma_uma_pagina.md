# SisTer — Roteiro de Transição em uma Página

**Finalidade:** orientar a equipe da referência funcional atual até a produção, usando marcos de maturidade definidos por evidências e não por calendário.

## Regra central

> **Alfa prova a arquitetura; Beta prova a integração; Gama prova a operação; Produção assume o compromisso.**

Os nomes Alfa, Beta e Gama são marcos internos. O versionamento técnico continua seguindo SemVer:

```text
0.2.x-prototype → 0.3.0-alpha.N → 0.4.0-beta.N → 0.9.0-gamma.N → 1.0.0
```

A **Gama** será sempre descrita também como *candidata à produção* ou *pré-produção*, pois esse nome não é universalmente padronizado.

---

## Estado da baseline e próximo ciclo

SEC-00, SEC-01, SEC-01A e SEC-01B estão concluídos: o `sisterd` foi retirado da
borda de produção, a autorização sensível usa capacidades com negação por
padrão e o bootstrap produtivo é local, de uso único e sem sessão. Esses itens
adiantam fundações do roteiro, mas não promovem o conjunto à Beta ou à produção.
SEC-01C e SEC-01D estão implementados e validados depois da tag `v0.2.5` e
formam a `v0.2.6`, junto ao MAES-SisTer/1.0. O SEC-02V aprovou a identidade
interna Ed25519 somente para operação interna, read-only e shadow; SEC-02M
separou o cliente Nexo do proxy legado e restringiu a emissão a uma rota exata.
Esse escopo forma a `v0.2.7`. Escrita depende de SEC-02R e produção externa
permanece bloqueada. SEC-03A definiu ADR-0020 e o perfil executável da borda;
SEC-03B/C/V continuam necessários antes da `v0.2.8`.

Consulte a [baseline de segurança do `sisterd`](./SISTERD_SECURITY_BASELINE.md)
e o [alinhamento com a EFE-SisTer/1.2](./EFE_SISTER_1_2_ALIGNMENT.md).

---

## 0. Pré-Alfa — congelar a referência

**Objetivo:** preservar o fluxo que funciona e impedir novas integrações pelo padrão provisório.

1. Criar tag e snapshot verificável.
2. Manter smoke tests de autenticação, Nexo e Clima.
3. Registrar túnel WebSocket, repasse de cookie, arquivo de autenticação e proxies específicos como dívida técnica bloqueante.
4. Marcar o estado como `development_prototype`.
5. Proibir novos blocos específicos de proxy no `sisterd`.

**Gate:** baseline reconstruível, testes executáveis e limitações formalmente registradas.

---

## 1. Alfa — construir as fundações

**Objetivo:** provar a arquitetura em ambiente interno.

1. Aprovar os ADRs centrais: papel do `sisterd`, gateway separado, adaptadores, PostgreSQL, capacidades e identidade assinada.
2. Publicar `sister.subsystem/1.0.0` com manifesto, health, readiness, capacidades, erros e auditoria.
3. Modularizar o `sisterd` sem mudar o comportamento externo.
4. Migrar usuários e sessões para PostgreSQL; guardar somente hash do token de sessão.
5. Integrar ao armazenamento transacional a revogação, a expiração e o
   bootstrap offline já endurecido; executar migração controlada.
6. Criar catálogo de capacidades e API `/api/me/capabilities`.
7. Emitir identidade interna assinada, curta e com audiência específica.
8. Validar primeiro no Nexo por uma rota de laboratório.

**Gate Alfa:**

- login, logout, revogação e reinício funcionam sem arquivo operacional;
- Nexo rejeita assinatura inválida, audiência errada, expiração e capacidade ausente;
- o novo caminho não encaminha cookie;
- testes unitários e de contrato aprovados;
- rollback documentado.

---

## 2. Beta — integrar pelo caminho definitivo

**Objetivo:** provar a integração completa de Nexo e Clima.

1. Comparar candidatos e registrar a escolha do gateway em ADR.
2. Configurar TLS, HTTP, WebSocket, limites, timeouts e remoção de cabeçalhos não confiáveis.
3. Implementar adaptador conformante no Nexo.
4. Implementar adaptador conformante no Clima.
5. Retirar o túnel WebSocket do `sisterd`.
6. Eliminar definitivamente o repasse do cookie aos subsistemas.
7. Aplicar capacidades no backend e na interface.
8. Criar registry no PostgreSQL e ativação por manifesto aprovado.
9. Executar suíte comum de conformidade.
10. Testar coexistência e rollback antes de retirar a rota antiga.

**Gate Beta:**

- Clima e Nexo passam na mesma suíte;
- WebSockets não consomem trabalhadores do núcleo;
- falha de um subsistema não bloqueia autenticação nem o outro;
- nenhuma rota específica de Clima ou Nexo precisa estar codificada no `main.cpp`;
- nova integração conformante pode ser registrada sem recompilar o núcleo.

---

## 3. Gama — provar a operação

**Objetivo:** transformar a Beta em candidata à produção.

1. Implantar logs correlacionados, métricas, dashboards e auditoria persistente.
2. Aplicar hardening de `systemd`, isolamento de segredos e política de rotação.
3. Executar testes de carga, segurança, falha, reinício e recuperação.
4. Testar backup e restauração.
5. Testar rotação de chaves sem interrupção indevida.
6. Criar e ensaiar runbooks.
7. Executar piloto controlado com usuários e dados autorizados.
8. Atualizar threat model e registro de riscos.
9. Realizar revisão formal de prontidão.

**Gate Gama:**

- nenhum risco crítico aberto;
- riscos altos tratados ou formalmente aceitos;
- metas de capacidade e latência atendidas;
- recuperação e rollback comprovados;
- alertas e runbooks testados;
- responsáveis operacionais definidos;
- aprovações de arquitetura, segurança, qualidade e domínio registradas.

---

## 4. Produção 1.0.0 — assumir o compromisso

1. Publicar artefatos assinados e digests.
2. Aplicar migrações verificadas.
3. Promover gateway, `sisterd` e adaptadores aprovados.
4. Monitorar a implantação e validar indicadores.
5. Remover o caminho legado e seus segredos.
6. Registrar aceite e iniciar manutenção regular.

**Aceite final:** o caminho provisório foi removido, as integrações são contratadas e auditáveis, e a equipe consegue operar, recuperar e evoluir o sistema sem depender da memória de quem o implementou.

---

## Evidência mínima para mudar de estágio

Toda promoção exige:

- **artefato versionado**;
- **teste reproduzível**;
- **registro de decisão ou aceite**;
- **responsável definido**.

Não há promoção por data, demonstração visual ou sensação de que “já está funcionando”. Funcionar abre a porta; engenharia decide se podemos atravessá-la.
