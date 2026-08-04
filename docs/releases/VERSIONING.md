# Política de identificação e versionamento do SisTer

## Revisão corrente do repositório

Além das versões de release, o SisTer usa uma revisão sequencial calculada do
primeiro-parent da `main`:

```text
R000142  release v0.2.10
R000163  baseline funcional do RAF/1.0
R000166  estado integrado corrente
```

`R######` ordena estados integrados para leitura humana. Não substitui o hash
Git, não é uma tag e não deve ser incrementado manualmente. O comando
`scripts/release/version-state.py` calcula a revisão atual, a revisão da
release, a revisão do RAF e a relação de ancestralidade.

A política exige que `main` não tenha histórico reescrito nem force-push. Se a
linha divergir, a verificação continua mostrando `DIVERGED`; a revisão
sequencial, sozinha, nunca prova ancestralidade.

## Quatro coisas diferentes

| Elemento | Exemplo | Significado |
| --- | --- | --- |
| Versão de engenharia | `0.2.10` | última baseline publicada em `VERSION` |
| Tag de engenharia | `v0.2.10` | commit imutável da baseline |
| Tag de produto | `prod-mvp-v0.1.1` | release operacional do produto |
| Documento normativo | `EFE-SisTer/1.7`, `RAF-SisTer/1.0` | versão independente de especificação ou diagnóstico |
| Revisão do repositório | `R000166` | ordem calculada do estado integrado |

## Estado de desenvolvimento

Depois de uma release, `main` entra em `development` e pode conter commits
posteriores à tag. Isso não é uma nova release. `VERSION` continua apontando
para a última versão publicada até o próximo gate de publicação.

O estado verificável da linha corrente está em
[`engineering/release/version-state.json`](../../engineering/release/version-state.json).
Cada release possui também um manifesto imutável, como
[`v0.2.10.yaml`](./v0.2.10.yaml). A relação entre o manifesto e o commit
observado é calculada por `scripts/release/version-state.py`.

## Gate de release

Uma nova release exige, no mesmo processo:

1. commit candidato identificado;
2. `VERSION` atualizado para a nova versão;
3. documento de release atualizado;
4. testes, gates e evidências encerrados;
5. decisão humana de publicação;
6. tag nova criada sem alterar tags anteriores;
7. estado do versionamento atualizado para `released`.

Antes do gate, a linguagem correta é “desenvolvimento posterior à baseline”,
“candidato” ou “release candidate”, nunca “release”.

## Estado atual

```text
última baseline: v0.2.10
última release de produto: prod-mvp-v0.1.1
linha corrente: main / development
próxima release: não definida
revisão corrente: calculada por scripts/release/version-state.py
```
