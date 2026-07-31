# ADR-0012: Módulos internos do Processo de Engenharia e SGE-SisTer

## Status

Aceita

## Contexto

O SisTer consolidou contratos, gates, verificador, atestações, histórico,
Centro de Engenharia e SGE-SisTer. Esse conjunto já governa a evolução técnica
da plataforma, mas ainda vive parcialmente misturado a documentos e scripts do
núcleo.

Extrair esse mecanismo para outro projeto agora seria prematuro: os contratos,
perfis, modelos e usos por subsistema ainda precisam ser validados em casos
reais. Ao mesmo tempo, deixar o processo amadurecer acoplado ao núcleo tornaria
a reutilização futura difícil.

## Decisão

O Processo de Engenharia e o SGE-SisTer serão inicialmente consolidados como
módulos internos do repositório SisTer, orientados por contratos e sem
dependência irreversível do núcleo.

A extração para um projeto independente só será reavaliada após evidência de
reutilização real entre componentes, inicialmente núcleo, Nexo e Clima.

## Diretrizes

- Declarar uma fronteira `engineering/` para modelos, perfis, checks e
  templates reutilizáveis.
- Manter scripts existentes funcionando durante a migração.
- Criar contratos versionados antes de mover semântica operacional.
- Parametrizar por componente e perfil, em vez de codificar conhecimento do
  núcleo.
- Não gerar aprovações automaticamente.
- Não transformar o Centro de Engenharia em executor remoto de gates.
- Medir reutilização antes de decidir extração.

## Consequências

- O SGE-SisTer passa a ter uma fronteira interna explícita.
- O repositório pode evoluir sem criar um framework abstrato prematuro.
- A equipe ganha um caminho de refatoração: declarar, contratar, parametrizar,
  validar e só então extrair.
- Mudanças futuras em maturidade devem evitar dependências diretas do runtime
  do `sisterd`.
