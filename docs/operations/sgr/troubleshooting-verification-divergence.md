# Troubleshooting de Divergência de Verificação

Este procedimento orienta a investigação quando o engine `compare` encontra
divergência entre `legacy` e `declarative`.

Referência arquitetural: [Engines de verificação e modos de governança](../../architecture/sgr/verification-engines-and-governance-modes.md).

## Quando usar

Use este procedimento quando:

- `compare` retornar resultados diferentes entre engines;
- um check passar em `legacy` e falhar em `declarative`, ou o inverso;
- a evidência gerada por um engine não corresponder à política esperada;
- houver suspeita de mudança silenciosa na semântica de um gate.

## Procedimento

1. Executar o gate com `--engine legacy`.
2. Executar o mesmo gate com `--engine declarative`.
3. Comparar código de saída, resultado técnico, blockers e evidências.
4. Identificar se a divergência está no perfil, no check delegado, no avaliador ou no mecanismo antigo.
5. Corrigir a causa quando a divergência for acidental.
6. Registrar a divergência quando ela for intencional ou temporariamente aceita.
7. Reexecutar com `--engine compare`.

## Classificação

| Tipo | Interpretação | Ação |
|---|---|---|
| Perfil incompleto | O declarativo não cobre uma regra existente | Atualizar perfil e checks |
| Regra legada obsoleta | O `legacy` aplica política que não deve continuar | Registrar decisão e planejar retirada |
| Evidência inconsistente | Os engines discordam no artefato produzido | Corrigir normalização ou schema |
| Falha de check delegado | Script externo quebrou ou mudou contrato | Corrigir script ou contrato |
| Mudança intencional | A política nova difere da antiga | Registrar ADR, DAI ou decisão equivalente |

## Registros mínimos

Uma divergência aceita deve registrar:

- gate e componente afetado;
- engine que passou e engine que falhou;
- evidências comparadas;
- causa identificada;
- decisão adotada;
- responsável;
- prazo de revisão ou remoção.

Enquanto a divergência não for resolvida ou formalmente aceita, `compare`
deve continuar sendo tratado como proteção da migração do verificador.
