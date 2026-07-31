# Sistema de Governança da Engenharia do SisTer

Encerrada a fase de validação do protótipo integrado. Inicia-se a consolidação
da arquitetura de produção, orientada por contratos, evidências e gates de
engenharia.

O SisTer deixa de evoluir por funcionalidades isoladas e passa a evoluir por
arquitetura governada.

## Papel

O Sistema de Governança da Engenharia do SisTer (SGE-SisTer) é o plano de
controle da evolução técnica da plataforma. Ele não substitui os subsistemas,
nem seus domínios científicos ou operacionais. Sua função é garantir que a
evolução do ecossistema seja decidida, implementada, testada, atestada e
promovida com base em evidências verificáveis.

## Fluxo de trabalho

```text
Arquitetura
        |
        v
Contrato
        |
        v
Pacote de trabalho
        |
        v
Implementação
        |
        v
Testes
        |
        v
Gate
        |
        v
Centro de Engenharia
        |
        v
Promoção do estágio
```

Antes de implementar uma mudança, a equipe deve responder:

> Em qual pacote de trabalho, em qual ADR e em qual gate esta mudança se
> encaixa?

Se a resposta não existir, a primeira tarefa é criar ou atualizar o registro
arquitetural correspondente.

## Componentes

| Componente | Papel | Local |
|---|---|---|
| Decisões arquiteturais | Registrar escolhas, alternativas e consequências | `docs/adr/` |
| Arquitetura de transição | Explicar o que construir e por quê | `docs/architecture/sister_transicao_prototipo_para_arquitetura_producao.md` |
| Roteiro Alfa-Beta-Gama | Definir ordem, estágio e critérios de saída | `docs/architecture/sister_roteiro_alfa_beta_gamma_uma_pagina.md` |
| Pacotes de trabalho | Converter arquitetura em incrementos governados | `docs/work-packages/` |
| Contratos | Tornar integrações e evidências verificáveis | `contracts/` |
| Gates | Declarar critérios de maturidade executáveis | `.sister/maturity.conf`, `scripts/verify-sister-maturity.sh` |
| Evidências | Registrar aprovações, relatórios e provas humanas | `docs/evidence/` |
| Atestações | Publicar resultado sanitizado dos gates | `.run/maturity/` |
| Centro de Engenharia | Apresentar estado, proveniência e evolução | `/admin/maturity` |

## Regra de promoção

Toda promoção de estágio exige quatro elementos:

- artefato versionado;
- teste reproduzível;
- registro de decisão, evidência ou aceite;
- responsável definido.

Não há promoção por data, demonstração visual ou percepção de progresso. Uma
funcionalidade pode funcionar e ainda permanecer bloqueada se faltar contrato,
isolamento, segurança, teste, recuperação, documentação ou aceite.

## Pacotes de trabalho

Pacotes de trabalho devem ser derivados do plano de transição e do roteiro de
maturidade. Um pacote mínimo deve registrar:

- objetivo arquitetural;
- estágio alvo;
- ADRs relacionadas;
- contratos afetados;
- evidências esperadas;
- checks ou gates impactados;
- riscos e rollback;
- responsável técnico.

Pacotes ativos:

- [WP-02 - Contrato comum de subsistema](../work-packages/WP-02-contrato-comum-subsistema.md)

## Fronteiras

O SGE-SisTer governa a evolução técnica, mas não deve concentrar domínios que
pertencem aos subsistemas.

- O núcleo SisTer governa identidade, contratos, autorização, catálogo e
  integração.
- O gateway protege e transporta HTTP/WebSocket.
- Adaptadores traduzem contratos e capacidades.
- Subsistemas preservam seus domínios.
- O Centro de Engenharia apresenta evidências e não executa gates.

## Estado atual

O protótipo integrado fica classificado como referência funcional de
desenvolvimento. O próximo ciclo é a consolidação Alfa, cuja finalidade é
provar fundações arquiteturais antes de expandir integrações.
