# SEC-03V-ENV — ambiente candidato privilegiado

**Estado:** `BLOCKED` até aplicação por operador privilegiado e preflight
`READY`  
**Responsável:** operação/infraestrutura do host  
**Revisor:** segurança e arquitetura  
**Resultado esperado:** ambiente candidato reproduzível, verificável e
reversível

## Limite da entrega

Este cartão materializa as contas, arquivos, unidades e permissões que o
`SEC-03V` avaliará. Ele não fecha o gate, não autoriza exposição externa, não
altera tags e não habilita escrita. O perfil continua restrito a ambiente
interno, loopback, HTTP/1.1, read-only e shadow.

O relatório executável é produzido por:

```bash
./scripts/sec03v_env_preflight.py \
  --haproxy-bin /usr/local/sbin/haproxy-3.2.22
```

O comando retorna `0` somente para `READY` e `2` para `BLOCKED`. O relatório
sanitizado fica em `.run/security/sec03v-env-preflight.json`; valores de
configuração e segredos nunca são copiados para ele.

## Pré-condições do operador

Antes de alterar o host:

1. confirmar worktrees limpos e registrar os commits do SisTer e do Nexo;
2. executar o pipeline integral na revisão que será instalada;
3. obter um executável HAProxy 3.2.22 ou posterior da linha 3.2 por canal
   aprovado, com proveniência e assinatura verificadas;
4. preparar certificado de candidato para o Host exato, sem reutilizar chave
   de produção;
5. preparar backup dos arquivos instalados existentes;
6. manter o Nexo `READY` e seu PostgreSQL acessível em loopback.

O wrapper Podman de `.run/gateway/haproxy-3.2.22` é suficiente para testes de
laboratório, mas não é um pacote candidato para `/usr/local/sbin`.

No Fedora 44 Workstation, a origem aprovada para este laboratório é o RPM local
`sister-haproxy-lab`, produzido e assinado pelo procedimento versionado em
[`packaging/haproxy/README.md`](../../packaging/haproxy/README.md). A instalação
usa DNF com verificação da chave dedicada e `localpkg_gpgcheck=1`; não há
`rpm-ostree` neste host. Build e assinatura não autorizam a instalação nem a
ativação do serviço sem a revisão operacional de HAPROXY-RPM-01.

HAPROXY-RPM-01 foi concluído no host candidato Fedora 44 pela transação DNF
`135`. A evidência verificável está em
[`HAPROXY-RPM-01.json`](../evidence/security/HAPROXY-RPM-01.json). Esse marco
satisfaz somente a proveniência do executável; SEC-03V-ENV permanece `BLOCKED`
até a aplicação privilegiada das identidades, configurações e unidades.

## Contas e grupos

As identidades canônicas são:

| Identidade | Função | Shell | Grupos |
| --- | --- | --- | --- |
| `sister` | executar `sisterd` | `nologin` | primário `sister` |
| `sister-gateway` | executar HAProxy | `nologin` | primário `sister-gateway`, suplementar `haproxy` |
| `haproxy` | autorizar leitura/escrita no socket | grupo, sem usuários interativos | `sister-gateway` |

O operador deve criar grupos e usuários como contas de sistema. Usuários
interativos no grupo `haproxy` bloqueiam o preflight.

## Instalação candidata

Os artefatos instalados devem corresponder byte a byte à revisão avaliada:

| Origem versionada | Destino | Proprietário e modo |
| --- | --- | --- |
| `build/apps/sisterd/sisterd` | `/opt/sister/build/apps/sisterd/sisterd` | `root:root 0755` |
| `web/` | `/opt/sister/web/` | `root:root`, diretórios `0755`, arquivos `0644` |
| commit avaliado | `/opt/sister/.sister-revision` | `root:root 0444` |
| `ops/systemd/sisterd.service` | `/etc/systemd/system/sisterd.service` | `root:root 0644` |
| `ops/systemd/sisterd.socket` | `/etc/systemd/system/sisterd.socket` | `root:root 0644` |
| `ops/systemd/sister-gateway.service` | `/etc/systemd/system/sister-gateway.service` | `root:root 0644` |
| `ops/tmpfiles.d/sister.conf` | `/etc/tmpfiles.d/sister.conf` | `root:root 0644` |
| configuração preparada fora do Git | `/etc/sister/sister.env` | `root:root 0600` |
| chave Ed25519 privada local | `/etc/sister/identity-private.pem` | `sister:sister 0600` |
| chave Ed25519 pública | `/etc/sister/identity-public.pem` | `root:root 0644` |
| certificado e chave TLS combinados | `/etc/sister/gateway/tls.pem` | `root:sister-gateway 0640` |
| CA do certificado candidato | `/etc/sister/gateway/ca.crt` | `root:root 0644` |

O diretório `/etc/sister` permanece `root:root 0750`, sem listagem para as
contas de serviço. ACLs nomeadas concedem somente travessia aos dois processos
que precisam alcançar arquivos governados abaixo dele:

```bash
sudo setfacl -m u:sister:--x,u:sister-gateway:--x /etc/sister
```

`/etc/sister/gateway` permanece `root:sister-gateway 0750`. A ACL do diretório
pai não concede leitura de `sister.env`, da chave Ed25519 ou do PEM TLS; os
modos e grupos de cada arquivo continuam decidindo esse acesso. O preflight
executa verificações de leitura sob as identidades `sister` e
`sister-gateway`, impedindo aprovação baseada apenas na visão privilegiada de
`root`.

O arquivo de ambiente parte de `.env.production.example`. Para o candidato,
`SISTER_ENABLE_NEXO_SIGNED_INTEGRATION=true` e os caminhos canônicos são
obrigatórios. A URL do banco e o `kid` são definidos pelo operador e não são
registrados em logs ou documentação.

A chave de identidade pode ser criada localmente pelo operador:

```bash
openssl genpkey -algorithm Ed25519 -out identity-private.pem
openssl pkey -in identity-private.pem -pubout -out identity-public.pem
```

Os arquivos temporários devem nascer sob `umask 077`, ser instalados com os
proprietários acima e removidos do diretório de preparação após a validação.

## Configuração candidata do gateway

Depois de instalar o PEM e os erros HTTP versionados em
`/etc/sister/gateway/errors`, renderizar como operador privilegiado:

```bash
sudo env \
  GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22 \
  GATEWAY_TLS_PEM=/etc/sister/gateway/tls.pem \
  GATEWAY_ALLOWED_HOST=sister-gateway.test \
  GATEWAY_CANONICAL_HOST=sister-gateway.test \
  GATEWAY_UPSTREAM_SOCKET=/run/sister/sisterd.sock \
  python3 scripts/render_gateway_config.py --scope candidate

sudo chown root:sister-gateway /etc/sister/gateway/haproxy.cfg
sudo chmod 0640 /etc/sister/gateway/haproxy.cfg
sudo /usr/local/sbin/haproxy-3.2.22 \
  -c -V -f /etc/sister/gateway/haproxy.cfg
```

O executável candidato deve pertencer a um RPM assinado e permanecer sem
divergência segundo `rpm -V`. Wrapper, cópia avulsa e `make install` são
rejeitados pelo preflight.

O escopo `candidate` fixa listener em `127.0.0.1:8443`, TLS 1.3, Host exato e
upstream único em `/run/sister/sisterd.sock`. Ele recusa saída fora de
`/etc/sister/gateway/haproxy.cfg` e não aceita fallback TCP.

## Ativação controlada

1. parar o runner de desenvolvimento pelo seu contrato, comprovando a
   propriedade do PID;
2. confirmar ausência de listener em `127.0.0.1:8000`;
3. executar `systemd-tmpfiles` para o arquivo versionado;
4. executar `systemctl daemon-reload`;
5. habilitar e iniciar apenas `sisterd.socket`;
6. validar `/run/sister` como `root:haproxy 0750`, com ACL de travessia
   `u:sister:--x` e sem leitura, listagem ou escrita adicional;
7. validar o socket como `sister:haproxy 0660`;
8. instalar, habilitar e iniciar `sister-gateway.service`;
9. executar novamente o preflight como root, preservando o relatório:

   ```bash
   sudo ./scripts/sec03v_env_preflight.py \
     --haproxy-bin /usr/local/sbin/haproxy-3.2.22 \
     --report /var/lib/sister-sec03v-env/sec03v-env-preflight.json
   ```

10. somente com `READY`, iniciar a matriz SEC-03V sem skips.

O preflight final confirma que o processo ativo corresponde ao binário nativo,
executa como `sister-gateway`, pertence ao grupo suplementar `haproxy`, escuta
somente em `127.0.0.1:8443`, completa TLS 1.3 com a CA candidata e alcança o
health check do `sisterd` com PostgreSQL no estado `connected`. Também deriva a chave pública da chave privada e
compara o par sem registrar seu conteúdo.

`sisterd.service` é ativado sob demanda pelo socket e não precisa ser habilitado
diretamente. Falha de ativação bloqueia o gate; é proibido abrir a porta 8000
como recuperação.

## Backup e rollback

Antes da instalação, copiar os destinos existentes para um diretório datado
sob `/var/lib/sister-sec03v-env/backups`, mantendo proprietário, modo e contexto
SELinux. Registrar no mesmo diretório os commits do SisTer/Nexo, checksum do
HAProxy e lista exata de arquivos substituídos. Nunca copiar segredos para o
repositório.

Rollback permitido:

1. parar e desabilitar `sister-gateway.service`;
2. parar `sisterd.service` e `sisterd.socket`;
3. restaurar conjuntamente binário, web, unidades, tmpfiles e configuração do
   backup selecionado;
4. executar `daemon-reload` e validar offline as unidades restauradas;
5. reativar somente o socket da versão restaurada;
6. executar o preflight correspondente à revisão restaurada.

Contas, banco, arquivo de autenticação e chaves não são apagados
automaticamente. A indisponibilidade externa é um rollback aceitável; listener
TCP, proxy legado, WebSocket ou TLS enfraquecido são proibidos.

## Critério de saída

`SEC-03V-ENV` termina somente quando todos os controles do relatório estiverem
`PASS`, o resultado for `READY` e segurança/arquitetura revisar a evidência. A
partir daí o ambiente pode executar `SEC-03V`; ele ainda não pode receber tag
ou declaração de prontidão produtiva.
