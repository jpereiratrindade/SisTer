# Sistema de Governança da Engenharia do SisTer

## Reprodutibilidade da verificação

Checks equivalentes dos motores legado e declarativo devem resolver para a
mesma evidência executável. O `smoke-flow` usa `scripts/ci/test-smoke.sh`, que
inicia um `sisterd` isolado em porta efêmera, executa a fronteira pública e o
encerra. `sge verify` não depende de uma execução operacional previamente ativa.

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
| Módulos de engenharia | Consolidar processo, governança e maturidade reutilizáveis | `engineering/` |
| Contratos | Tornar integrações e evidências verificáveis | `contracts/` |
| Gates | Declarar critérios de maturidade executáveis | `engineering/maturity/`, `scripts/maturity/evaluator.py` |
| Evidências | Registrar aprovações, relatórios e provas humanas | `docs/evidence/` |
| Atestações | Publicar resultado sanitizado dos gates | `.run/maturity/` |
| Centro de Engenharia | Apresentar estado, proveniência e evolução | `/admin/maturity` |

## Evolução rastreável

O SGE-SisTer possui três níveis de leitura sobre maturidade:

1. **Fotografia:** a última execução publicada mostra o estado atual do gate.
2. **Histórico:** cada execução feita por `scripts/sge maturity publish`
   arquiva uma atestação em `.run/maturity/history/` e atualiza o índice.
3. **Tendência:** métricas de permanência por estágio, regressões, estabilidade
   e dimensões de engenharia serão derivadas do histórico acumulado.

O comando `scripts/verify-sister-maturity.sh` permanece como compatibilidade do
Core durante a transição. O módulo declarativo em `engineering/maturity/`,
executado por `scripts/maturity/evaluator.py`, é a direção arquitetural.
Operacionalmente, a entrada preferencial é `scripts/sge maturity`. O
rastreamento automático acontece quando o gate é executado pelo fluxo de
publicação `scripts/sge maturity publish`.

A entrada cotidiana completa é `./scripts/sge verify`. Ela executa a suíte de
qualidade do repositório e publica a maturidade de todos os componentes
localmente resolvíveis. O engine é selecionado automaticamente por componente:
`compare` para o Core e `declarative` para componentes federados.

## Modularização interna

O Processo de Engenharia e o SGE-SisTer serão consolidados inicialmente como
módulos internos em `engineering/`, orientados por contratos e sem dependência
irreversível do núcleo. A extração para projeto independente só será avaliada
após evidência de reutilização real entre componentes.

Referências:

- [Arquitetura do Processo de Engenharia, SGE-SisTer e Módulo de Maturidade](../architecture/sister_arquitetura_processo_engenharia_sge_maturidade.md)
- [Tutorial do Módulo de Maturidade](../../engineering/maturity/README.md)
- [ADR-0012](../adr/ADR-0012-internal-engineering-modules.md)

## Roadmap do SGE

| Versão | Foco | Resultado esperado |
|---|---|---|
| SGE 1.0 | Fotografia governada | última atestação, Centro de Engenharia e promoção por evidência |
| SGE 1.1 | Histórico automático | execuções e mudanças de estágio arquivadas sem registro manual |
| SGE 1.2 | Métricas e tendências | tempo por estágio, regressões, estabilidade e saúde da engenharia |
| SGE 2.0 | Radar de Engenharia | riscos, gargalos e próximos bloqueadores derivados das evidências |

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
