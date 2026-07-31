# Modos de Verificação e Governança — resumo para o SGR

> **O engine determina como a maturidade é verificada; o modo de governança determina que autoridade o resultado possui.**

## Engines

- **`compare` — padrão durante a transição:** executa `legacy` e `declarative` e detecta divergências.
- **`declarative` — motor de destino:** executa os checks definidos nos perfis declarativos.
- **`legacy` — diagnóstico temporário:** reproduz o comportamento antigo e ajuda a investigar divergências.

## Governança

- **`shadow`:** o componente é avaliado, aparece no SGR e produz evidências, mas sua falha não bloqueia a promoção global.
- **`governed`:** a falha pode bloquear a promoção dentro do escopo definido.

## Regra operacional

```text
compare divergiu
→ testar legacy e declarative isoladamente
→ comparar evidências
→ corrigir ou registrar a divergência

shadow falhou
→ registrar, alertar e acompanhar
→ não bloquear fora do escopo

governed falhou
→ bloquear o escopo afetado
→ diagnosticar, corrigir ou aplicar exceção formal
```

> **`compare` protege a migração do verificador; `shadow` protege a evolução federada do ecossistema.**

A passagem de `shadow` para `governed` exige, conjuntamente:

1. maturidade técnica;
2. criticidade arquitetural;
3. responsabilidade operacional formal.

**Maturidade não implica automaticamente poder de bloqueio.**
