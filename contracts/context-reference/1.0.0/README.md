# SisTer Context Reference 1.0.0

Contrato mínimo para identificar, sem duplicar autoridade de domínio,
uma entidade que participa de uma composição contextual federada.

## Objetivo

Uma referência contextual responde somente:

1. qual autoridade possui a identidade referenciada;
2. qual classe de identidade aquela autoridade declara;
3. qual é o identificador opaco atribuído pela autoridade.

Exemplo:

```json
{
  "authority": "authority-alpha",
  "kind": "project",
  "id": "project-001"
}
```

O SisTer pode transportar, comparar e compor referências desse tipo sem
assumir a semântica interna das classes declaradas por qualquer
participante.

## Invariantes

- `authority` identifica a autoridade que possui a referência.
- `kind` identifica a classe da referência dentro daquela autoridade.
- `id` é opaco para consumidores externos à autoridade.
- igualdade exige a igualdade da tripla `(authority, kind, id)`.
- nomes, títulos, labels e descrições NÃO constituem identidade federativa.
- uma referência NÃO transfere autoridade de domínio ao SisTer.
- duas referências presentes no mesmo documento NÃO são, por si só,
  prova de relação entre elas.

## Fora de escopo

Este contrato não define:

- vínculo entre referências;
- projeto ativo;
- atividade ativa;
- território ativo;
- intervalo temporal;
- conteúdo científico;
- estado factual;
- evidência;
- ação;
- continuidade.

Esses conceitos serão definidos por contratos próprios quando houver
autoridade e evidência suficientes.

## Regra constitucional

O SisTer pode conhecer a identidade federativa de uma referência e
compor relações explicitamente declaradas, mas não deve reconstruir
relações de domínio por igualdade de nomes, labels ou outros atributos
de apresentação.
