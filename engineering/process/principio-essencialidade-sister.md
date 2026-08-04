# SisTer - Principio da Essencialidade

Todo elemento do SisTer deve responder a uma pergunta:

> Se removermos este elemento, o SisTer deixa de cumprir seu proposito?

Se a resposta for nao, esse elemento nao pertence ao nucleo do SisTer.

## Nucleo operacional

O SisTer existe para transformar capacidades disponiveis em conhecimento operacional por meio de um ciclo reflexivo governado:

```text
Necessidade
-> Capacidade
-> Contrato
-> Execucao
-> Observacao
-> Avaliacao
-> Recomendacao
-> Nova decisao
```

Nada deve existir no nucleo sem contribuir diretamente para esse ciclo.

## Centro de Engenharia

O Centro de Engenharia governa apenas:

- capacidades;
- contratos;
- criterios;
- autorizacoes;
- observacoes;
- avaliacoes;
- recomendacoes;
- conhecimento operacional.

PDE, Kanban, Sprint, Backlog, Issue, Pull Request, Git e tarefas de desenvolvimento pertencem a engenharia do desenvolvimento do software. Eles podem existir fora do nucleo, mas nao definem o modelo conceitual do SisTer.

## Reflexividade

Todo comportamento operacional deve responder:

```text
O que era esperado?
-> O que aconteceu?
-> Ha diferenca?
-> O que recomendamos fazer?
```

Nao existe reflexividade fora desse ciclo.

## Cibernetica governada

Nenhuma recomendacao altera o sistema diretamente.

```text
Recomendacao
-> Decisao da engenharia
-> Nova configuracao
-> Nova execucao
-> Nova observacao
```

## Regra de implementacao

Adicionar codigo apenas quando ele tornar o ciclo operacional mais completo.

Adicionar documentacao apenas quando ela definir contratos ou principios permanentes.

Todo o restante e ferramenta de desenvolvimento e deve permanecer fora do modelo conceitual do SisTer.
