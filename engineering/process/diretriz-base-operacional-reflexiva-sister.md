# Diretriz de Implementação - Base Operacional Reflexiva do SisTer

## Decisão

O Centro de Engenharia deve deixar de representar apenas como o SisTer está sendo desenvolvido e passar a mostrar também como o SisTer opera, observa e avalia processos aprovados.

O PDE permanece, mas limitado à gestão da engenharia. A nova prioridade é materializar uma Base Operacional de Conhecimento, composta por propósitos, funções e processos aprovados, versionados e aplicáveis.

## Separação obrigatória

| Camada | Responsabilidade |
|---|---|
| PDE | Planejar e governar mudanças no SisTer |
| Base Operacional | Definir como o SisTer deve operar |
| Operação | Registrar instâncias, eventos e evidências |
| Reflexividade | Comparar esperado x observado e recomendar |
| Autoridade humana | Aprovar estruturas e decisões críticas |

## Entrega inicial

```text
PurposeDefinition
-> FunctionDefinition
-> OperationalProcessDefinition
-> aprovação humana
-> ReferenceSnapshot
-> ProcessInstance
-> FunctionExecution
-> ProcessObservation
-> OperationalAssessment
-> recomendação
```

## Regra de autoridade

O engenheiro aprova a estrutura operacional, não cada execução comum.

A aprovação deve definir propósito, funções permitidas, ordem e pré-condições, entradas e saídas, evidências obrigatórias, critérios de conformidade, pontos de decisão humana e nível de autoridade concedido ao SisTer.

## Critério de aceite

A entrega estará concluída quando o SisTer conseguir demonstrar, com dados persistidos:

1. qual propósito rege uma operação;
2. qual processo aprovado será usado;
3. quais funções eram esperadas;
4. o que foi executado;
5. quais evidências foram observadas;
6. qual diferença existe entre esperado e observado;
7. qual recomendação foi produzida;
8. qual decisão humana ainda é necessária.

## Fora de escopo agora

- integrar subsistemas reais;
- automatizar decisões irreversíveis;
- usar IA como substituta da autoridade humana;
- transformar o PDE no motor operacional;
- ampliar o Kanban.

## Frase guia

O engenheiro aprova a estrutura operacional; o SisTer instancia, observa, compara e recomenda.
