# `sister.context-binding/1.0.0`

Contrato mínimo para representar um vínculo factual e atribuível entre duas
identidades contextuais pertencentes a autoridades de domínio.

## Escopo

Um binding contém exatamente os elementos necessários para afirmar:

```text
subject
authority + kind + id
        │
        │ relation
        ▼
object
authority + kind + id

declared_by = autoridade que declarou o vínculo
```

`subject` e `object` reutilizam a referência definida por
`sister.context-reference/1.0.0`.

A identidade continua pertencendo à autoridade de domínio. Este contrato não
cria identidade concorrente no SisTer.

## Semântica

- `binding_id` identifica a declaração de vínculo.
- `relation` é um token semântico declarado pela autoridade; este contrato não
  define uma ontologia global de relações.
- `subject` é a referência de origem.
- `object` é a referência de destino.
- `declared_by` identifica a autoridade responsável por declarar o vínculo.
- `provenance_ref`, quando presente, aponta para a proveniência da declaração.
- `evidence_refs`, quando presentes, apontam para evidências relacionadas à
  declaração.

Nomes, títulos, labels e descrições NÃO estabelecem vínculo.

A relação é declarada, não inferida pelo SisTer.

Uma coincidência textual como:

```text
"Bagé" == "Bagé"
```

NÃO constitui prova de identidade nem de relação.

O binding não transfere autoridade de domínio ao SisTer.

## Relação com `sister.relation/1.0.0`

`sister.relation/1.0.0` NÃO é reutilizado para este propósito.

Esse contrato descreve relações governadas entre participantes, papéis,
capability grants, fronteiras de autoridade, política de evidência e
governança. Além disso, permanece `DRAFT / NOT RUNTIME-NORMATIVE`.

`context-binding/1.0.0` possui escopo deliberadamente menor: declarar uma
aresta factual entre duas referências contextuais já identificáveis.

## Fora de escopo

Este contrato não define:

- ontologia universal;
- grafo global;
- catálogo central de relações;
- inferência por nomes;
- descoberta automática de vínculos;
- ranking;
- recomendação;
- motor semântico;
- transferência de autoridade;
- armazenamento central de contexto.

Essas capacidades não são necessárias para o `WEB-CONTENT-02B0-B`.

## Condição de suficiência

O contrato está completo para esta missão quando consegue representar,
inequivocamente:

```text
REF A
authority + kind + id
        │
        │ relation
        ▼
REF B
authority + kind + id

declared_by
provenance/evidence quando aplicável
```

Nada além disso pertence ao `WEB-CONTENT-02B0-B`.
