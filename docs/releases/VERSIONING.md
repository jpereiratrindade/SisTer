# Política de versionamento do SisTer

## Quatro coisas diferentes

| Elemento | Exemplo | Significado |
| --- | --- | --- |
| Versão de engenharia | `0.2.10` | última baseline publicada em `VERSION` |
| Tag de engenharia | `v0.2.10` | commit imutável da baseline |
| Tag de produto | `prod-mvp-v0.1.1` | release operacional do produto |
| Documento normativo | `EFE-SisTer/1.7`, `RAF-SisTer/1.0` | versão independente de especificação ou diagnóstico |

## Estado de desenvolvimento

Depois de uma release, `main` entra em `development` e pode conter commits
posteriores à tag. Isso não é uma nova release. `VERSION` continua apontando
para a última versão publicada até o próximo gate de publicação.

O estado verificável da linha corrente está em
[`engineering/release/version-state.json`](../../engineering/release/version-state.json).

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
```
