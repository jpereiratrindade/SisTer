# ADR-0025 - Versionamento explícito do desenvolvimento e das releases

## Status

Aceita em 2026-08-03.

## Contexto

O SisTer possui uma linha de baseline de engenharia (`v0.2.x`), uma linha de
produto (`prod-mvp-*`) e versões próprias para EFE, RAF e PDE. O desenvolvimento
posterior à tag `v0.2.10` avançou em `main` enquanto `VERSION` continuou
registrando a última versão publicada. Sem uma convenção explícita, isso pode
ser confundido com divergência ou com uma release não publicada.

## Decisão

`VERSION` representa a última versão publicada da linha de engenharia. O
trabalho posterior à última tag é estado `development` e não altera tags
existentes nem constitui release.

O estado deve ser lido junto com
[`docs/releases/VERSIONING.md`](../releases/VERSIONING.md) e
[`engineering/release/version-state.json`](../../engineering/release/version-state.json).

Uma release somente existe quando versão, commit, evidências, decisão de
publicação e tag são reconciliados no mesmo gate. Tags são imutáveis.

## Regras

- `main` pode avançar além da última release;
- `VERSION` não muda por commit de desenvolvimento;
- toda mudança de linha de release atualiza o registro de estado e o documento
  de release correspondente;
- tags `v*` e `prod-mvp-*` nunca são movidas ou sobrescritas;
- uma tag de produto não substitui a tag de baseline de engenharia;
- EFE, RAF e PDE possuem versionamento documental independente e devem declarar
  commit, baseline e relação normativa;
- nenhum commit pode ser chamado de release sem gate e decisão explícitos.

## Consequência

O estado atual pode ser descrito sem ambiguidade como: desenvolvimento em
`main`, posterior à baseline `v0.2.10`, ainda não publicado como nova release.
