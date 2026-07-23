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

| Projeto | Recurso | Desenvolvimento | Teste |
| --- | --- | --- | --- |
| SisTer | HTTP | 8000 | 8001 |
| SisTer | PostgreSQL | 55434 | 55435 |
| MorfoCampo | HTTPS | 8011 | - |
| DroneOps | HTTPS | 8012 | - |
| Sister-Studio | HTTPS público | 8443 | - |
| Sister-Studio Audio | HTTP interno | 18013 | - |
| Sister-Studio Voz | HTTP interno | 18043 | - |
| Sister-Studio Vídeo | HTTP interno | 18014 | - |
| Sister-Studio Certificado | HTTP | 8088 | - |
| Sister-Studio PostgreSQL | PostgreSQL | 55433 | - |
| Radar-Sister | HTTP | 8765 | - |
| Radar-Sister | PostgreSQL | 55432 | - |

O registro tambem inclui projetos locais nao integrados que reservam recursos,
pois eles podem colidir no mesmo host.

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

## Pendencias encontradas na auditoria

- o container antigo do LabGP declara 5432, mas sua reserva passa a ser 55436;
- `governanca_db` declara 55432, mas sua reserva passa a ser 55437;
- esses containers estao parados e precisam ser recriados pelas configuracoes
  de origem antes de voltarem a executar;
- o pipeline `inmet_000` usa o PostgreSQL do VGAF em 5434 e deve ser tratado
  como consumidor, nao como dono da porta;
- ha credencial de PostgreSQL escrita diretamente no Compose de `inmet_000`;
  ela deve ser removida do arquivo versionado e rotacionada.
