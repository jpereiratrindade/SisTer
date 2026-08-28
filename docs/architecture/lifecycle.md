# Arquitetura Sistêmica — Ciclo de Vida Operacional do SisTer

Este documento formaliza a generalização da arquitetura de ciclo de vida do SisTer, unificando os ambientes operacionais desde a alteração do código-fonte até a implantação em produção.

---

## 1. O Contraste Histórico: Da Arquitetura Legada (Apache) ao SisTer Declarativo

A evolução operacional do SisTer marca uma ruptura ontológica com paradigmas clássicos de infraestrutura manual:

| Dimensão | Paradigma Histórico (Legado / Apache) | Paradigma SisTer Declarativo (OPS-08) |
| :--- | :--- | :--- |
| **Topologia** | Estática, baseada em arquivos de configuração manuais (`/etc/apache2/`, vhosts fixos) | Declarativa e derivada dinamicamente por contratos normativos (`sister.component/1.0.0`) |
| **Identidade de Componentes** | Caminhos absolutos hardcoded no servidor | Subsistemas autodescritos com identidade lógica e interfaces padronizadas |
| **Acoplamento de Runtime** | Serviços acoplados ao host com portas fixas e colisões frequentes | Bindings e portas efêmeras alocadas sob contrato (`sister.infra.deployment/1.0.0`) |
| **Manutenção e Recuperação** | Intervenção reativa e manual do operador sob incidentes | Manutenção Reflexiva Automatizável (`REARIT-P001`): diagnóstico factual e `repair` mínimo |
| **Promoção entre Ambientes** | Cópia manual de arquivos (`scp`, `rsync`) com risco de rebuild silencioso | Promoção formal com evidência selada: a mesma candidata qualificada no LAB é promovida |
| **Segurança e TLS** | Certificados gerados ad-hoc ou chaves compartilhadas em repositório | Autoridade CA estrita, segregação de segredos e validação formal de certificados externos |
| **Governança de Produção** | Scripts mutantes executados com privilégios irrestritos | Planos selados deterministicamente por hash SHA-256 e travas institucionais de autoridade |

---

## 2. Diagrama Sistêmico de Ciclo de Vida

```text
+-----------------------------------------------------------------------------------+
|                                  SOURCE LEVEL                                     |
|           Contratos: sister.component/1.0.0 | sister.subsystem/1.0.0              |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                             DISCOVER & QUALIFICATION                             |
|          Qualificação formal de código-fonte, build e testes de unidade           |
|                (sister-component qualify | sister-composition qualify)             |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                               CANDIDATE CREATION                                  |
|            Materialização imutável de commits e artefatos qualificados            |
|                            (sister-candidate create)                              |
+-----------------------------------------------------------------------------------+
                         │                                    │
                         ▼                                    ▼
       +------------------------------------+   +------------------------------------+
       |            DEV PREVIEW             |   |              LAB PLAN              |
       |    Sessão temporária em loopback   |   |   Projeção determinística de LAB   |
       |   (zero resíduos, zero mutação)    |   |      (sister-reconcile plan)       |
       +------------------------------------+   +------------------------------------+
                         │                                    │
                         ▼                                    ▼
       +------------------------------------+   +------------------------------------+
       |            DEV VERIFY              |   |             LAB APPLY              |
       |     Validação de saúde do daemon   |   |  Reconciliação transacional no LAB |
       +------------------------------------+   |      (sister-reconcile apply)      |
                                                +------------------------------------+
                                                              │
                                                              ▼
                                                +------------------------------------+
                                                |             LAB VERIFY             |
                                                |     Pós-verificação obrigatória    |
                                                |    (sister-workstation verify)     |
                                                +------------------------------------+
                                                              │
                                                              ▼
                                                +------------------------------------+
                                                |      REFLEXIVE MAINTENANCE        |
                                                | Drift factual? -> auto-repair      |
                                                | (REARIT-P001 / workstation repair) |
                                                +------------------------------------+
                                                              │
                                                              ▼
+-----------------------------------------------------------------------------------+
|                                PROMOTION EVIDENCE                                 |
|            Avaliação de elegibilidade: WHAT WAS VERIFIED = WHAT IS PROMOTED       |
|                 (status PROMOTABLE, pureza de fontes, LAB verificado)             |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                                 PRODUCTION PLAN                                   |
|             Projeção em layout FHS e cálculo de digest canônico SHA-256           |
|                            (sister-production plan)                               |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                             INSTITUTIONAL AUTHORITY                               |
|        Travas obrigatórias: PRODUCTION_APPROVED=YES + confirmação do operador      |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                        PRODUCTION APPLY (FHS SANDBOX)                             |
|          Aplicação atômica em /opt/sister, rollback transacional e auditoria      |
|                            (sister-production apply)                              |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                           PRODUCTION VERIFY & EVIDENCE                            |
|             Cadeia de rastreabilidade genealógica (REARIT-P004)                   |
+-----------------------------------------------------------------------------------+
```

---

## 3. Os Cinco Ambientes e Estados Operacionais

1. **DEV**: Espaço de iteração rápida do desenvolvedor. Permite testar componentes autônomos via DEV Preview em loopback temporário sem alterar releases de workstation ou afetar o gateway do ecossistema.
2. **LAB**: O ambiente de laboratório e estação de trabalho cotidiana. Governa a composição integrada dos subsistemas através de reconciliação declarativa (`sister-reconcile`), controlando releases em `/var/home/.../.local/share/sister` com links atômicos `current` e `previous`.
3. **MAINTENANCE**: A capacidade reflexiva contínua. Observa divergências físicas no host (permissões, symlinks rompidos, daemons caídos com porta livre), executando correções estritamente mínimas ou falhando fechado (`fail-closed`) diante de corrupção ou invasão de portas por terceiros.
4. **PROMOTION**: Fronteira epistêmica de qualificação. Avalia factualmente se a candidata cumpre todos os requisitos normativos e de teste no LAB, emitindo certificado de promoção selado antes que qualquer plano de produção possa ser emitido.
5. **PRODUCTION**: O ambiente institucional governado. Adota padrão FHS (`/opt/sister`, `/etc/sister`, `/var/lib/sister`, `/run/sister`), plano imutável selado com digest SHA-256, travas institucionais de autoridade humana e rollback automático.

---

## 4. Invariante de Fronteira Institucional

> [!IMPORTANT]
> A infraestrutura institucional real é governada por autoridade delegada (`REARIT-P005`). A implantação sobre clusters ou servidores reais de produção depende de mandato administrativo externo e permanece **NÃO EXECUTADA E NÃO AUTORIZADA POR ESTA MISSÃO**, sendo comprovada exclusivamente em sandboxes herméticos auditados.
