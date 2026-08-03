# Governanca local dos projetos integrados

## Fonte unica

Projetos que integram o SisTer continuam autonomos, mas devem consultar este
repositorio antes de criar ou alterar recursos locais. O registro normativo e:

```text
config/local_resources.json
```

Ele reserva portas, nomes de containers e volumes para os ambientes locais.
Uma mudanca nesses recursos deve atualizar primeiro o registro central e depois
o projeto consumidor, na mesma entrega coordenada.

## Descoberta do SisTer

Cada repositorio integrado deve conter `SISTER_INTEGRATION.md`. O arquivo aponta
para esta governanca e define como localizar a raiz:

1. usar `SISTER_HOME`, quando definido;
2. procurar um repositorio irmao `SisTer`;
3. no layout deste laboratorio, usar `dev/cpp/SisTer`;
4. interromper a alteracao de infraestrutura se a fonte central nao estiver
   disponivel.

O vinculo e um arquivo pequeno, e nao um symlink absoluto, para continuar
funcionando quando os repositorios forem clonados separadamente.

## Descoberta dos subsistemas

O SisTer resolve repositórios integrados por contrato, sem caminhos absolutos no
Git:

1. `SISTER_WORKSPACE_ROOT` define a raiz comum do workspace;
2. `repository` em `config/local_resources.json` é resolvido abaixo dessa raiz;
3. `SISTER_REPOSITORY_ROOT_<ID>` sobrescreve um projeto específico quando teste,
   candidato ou produção usam outro layout;
4. sem variáveis, o layout local padrão é derivado da raiz do SisTer.

Exemplos:

```bash
export SISTER_WORKSPACE_ROOT=/run/media/jpereiratrindade/labeco10T/dev
export SISTER_REPOSITORY_ROOT_SISTER_NEXO=/opt/sister-nexo
```

As variáveis por projeto usam o ID normalizado em maiúsculas, com caracteres não
alfanuméricos convertidos para `_`.

Para diagnosticar uma máquina nova sem iniciar serviços:

```bash
python3 scripts/subsystems/ensure.py --environment dev --check
```

O comando identifica repositórios governados com `SISTER_INTEGRATION.md`, lista
contratos presentes fora da seleção executável e, quando algum subsistema
governado estiver ausente, informa a variável `SISTER_REPOSITORY_ROOT_<ID>` que
deve receber o caminho do repositório.

## Recursos sujeitos a coordenacao

- portas TCP/UDP, inclusive HTTP, HTTPS, PostgreSQL e servicos auxiliares;
- nomes de containers, pods, redes e projetos Compose;
- nomes de volumes persistentes;
- nomes mDNS, hosts locais e binds em `0.0.0.0`;
- caminhos compartilhados, sockets, arquivos PID e diretorios de runtime;
- bancos ou schemas compartilhados entre projetos;
- credenciais e variaveis de ambiente, que nunca devem entrar no registro com
  valores secretos.

## Alocacao atual

Durante validação de referência, somente `sister_reference` possui acesso
operacional. Demais integrações listadas abaixo são reservas históricas em
quarentena e não integram perfis oficiais, catálogo vigente ou roteamento.

| Projeto | Recurso | Desenvolvimento | Teste |
| --- | --- | --- | --- |
| SisTer | HTTP | `127.0.0.1:8000` | `127.0.0.1:8001` |
| SisTer | PostgreSQL | 55434 | 55435 |
| SisTer-Campo | API HTTP local | `127.0.0.1:8013` | - |
| SisTer-Campo | PostgreSQL | 55438 | - |
| SisTer Nexo | HTTP local | `127.0.0.1:8015` | - |
| SisTer Nexo | PostgreSQL | 55439 | - |
| Nexo-Compras | HTTP interno do Nexo | `127.0.0.1:8016` | - |
| Nexo-Compras | PostgreSQL | 55440 | - |
| MorfoCampo (não cadastrado) | HTTPS reservada | 8011 | - |
| DroneOps (não cadastrado) | HTTPS reservada | 8012 | - |
| Sister-Studio | HTTPS interno | 18443 | acesso externo somente pelo gateway SisTer |
| Sister-Studio Audio | HTTP interno | 18013 | - |
| Sister-Studio Voz | HTTP interno | 18043 | - |
| Sister-Studio Vídeo | HTTP interno | 18014 | - |
| Sister-Studio Certificado | HTTP interno | `127.0.0.1:8088` | - |
| Sister-Studio PostgreSQL | PostgreSQL | 55433 | - |
| Radar-Sister (não cadastrado) | HTTP reservado | 8765 | - |
| Radar-Sister | PostgreSQL | 55432 | - |
| Sister-Clima | HTTP interno | `127.0.0.1:8501` | acesso externo somente pelo SisTer |

O registro tambem inclui projetos locais nao integrados que reservam recursos,
pois eles podem colidir no mesmo host.

O repositório `cpp/sister_compras` está registrado como **Nexo-Compras**,
dependência contratual do `sister_nexo`. Sua execução pode ser garantida pelo
orquestrador raiz, mas ele não integra diretamente com o SisTer. A porta
PostgreSQL `55440`, o container `nexo-compras-dev-db` e o volume
`nexo_compras_dev_pgdata` são exclusivos.

## Regra operacional

Antes de adicionar ou mudar um recurso:

1. consultar `config/local_resources.json`;
2. escolher uma alocacao ainda nao registrada;
3. executar `python3 scripts/validate_local_resources.py`;
4. atualizar a configuracao e a documentacao do projeto consumidor;
5. validar os ambientes que podem executar simultaneamente;
6. registrar o projeto novo no SisTer antes de publicar.

O PostgreSQL sempre escuta em `5432` dentro do container; o registro coordena a
porta publicada no host.

## Inicializacao governada

Projetos integrados podem declarar `orchestration` no registro central. A
declaracao contém a URL local de saúde, o comando de inicialização sem shell, o
prazo de prontidão e se a indisponibilidade impede a subida do SisTer.

No perfil `dev-ecosystem`, `scripts/run_all.sh` executa
`scripts/subsystems/ensure.sh` depois de validar e iniciar o núcleo:

1. consulta a saúde e confirma a identidade esperada de cada projeto com
   política `ensure-running`;
2. preserva processos que já estejam saudáveis;
3. inicia somente comandos e repositórios explicitamente registrados;
4. informa divergência de fontes sem executar atualização implícita; a
   reconciliação exige `--update-subsystems`;
5. aguarda a saúde e grava logs em `.run/subsystems/`;
6. distingue serviços já ativos daqueles iniciados ou atualizados pelo SisTer;
7. trata porta ocupada com resposta inválida como degradação, sem iniciar um
   processo duplicado;
8. informa degradações opcionais como `PASS_WITH_DEGRADATION` e bloqueia
   componentes obrigatórios com código `2`.

O SisTer é o orquestrador raiz desse fluxo. Comandos `run_all.sh` dos projetos
integrados operam somente dentro da própria fronteira e nunca iniciam o SisTer.
Essa direção única evita dependência invertida e ciclos de inicialização.

O perfil `test-core` não inicia subsistemas. Os perfis executáveis vivem em
`config/run_profiles.json`: `dev-core` valida somente o núcleo,
`dev-ecosystem` trata os componentes como opcionais,
`dev-ecosystem-strict` bloqueia qualquer degradação e `sec-03v` exige HAProxy
real e Nexo. Este último valida pré-requisitos, mas não fecha SEC-03V nem gera
aprovação. `quality.json` permanece restrito à árvore; o resultado composto é
gravado em `run-all-status.json`. Nenhum segredo pode ser registrado no bloco
de ambiente da orquestração nem impresso pelo resumo do ambiente.

## Pendencias encontradas na auditoria

- o container antigo do LabGP declara 5432, mas sua reserva passa a ser 55436;
- `governanca_db` declara 55432, mas sua reserva passa a ser 55437;
- esses containers estao parados e precisam ser recriados pelas configuracoes
  de origem antes de voltarem a executar;
- o pipeline `inmet_000` usa o PostgreSQL do VGAF em 5434 e deve ser tratado
  como consumidor, nao como dono da porta;
- ha credencial de PostgreSQL escrita diretamente no Compose de `inmet_000`;
  ela deve ser removida do arquivo versionado e rotacionada.
