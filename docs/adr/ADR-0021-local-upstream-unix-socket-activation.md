# ADR-0021: Isolamento local do upstream por socket Unix ativado pelo systemd

## Status

Aceita — ISO-01 encerrado em laboratório como `LAB_PROVEN_WITH_RESTRICTIONS`

## Contexto

SEC-00 retirou o `sisterd` da borda externa e SEC-03B/03C materializaram o
gateway especializado. O backend ainda usava `127.0.0.1:8000`; loopback impede
acesso remoto, mas não diferencia o gateway de outros processos locais.

ISO-01 deve impedir que processos locais comuns sem a identidade ou o grupo
autorizados alcancem o `sisterd`, sem fazê-lo confiar automaticamente em
headers de origem, autoridade ou correlação. Essa confiança continua
condicionada a SEC-03V.

## Decisão

O transporte produtivo de entrada do `sisterd` é HTTP/1.1 sobre o socket Unix
canônico:

```text
/run/sister/sisterd.sock
```

O `systemd` cria o socket antes do processo, com `Accept=no`, e entrega
exatamente um descritor de escuta. O processo exige
`LISTEN_FDNAMES=sisterd-http` e valida `LISTEN_PID`, `LISTEN_FDS`, descritor 3,
`AF_UNIX`, `SOCK_STREAM`, `SO_ACCEPTCONN` e o caminho observado por
`getsockname`. Ausência ou divergência termina o arranque.

```text
HAProxy (grupo haproxy)
   │ HTTP/1.1 sobre AF_UNIX
   ▼
/run/sister/sisterd.sock  sister:haproxy 0660
   ▼
sisterd (usuário sister)
```

O diretório `/run/sister` é criado por `systemd-tmpfiles` como
`root:haproxy 0750`. O usuário do serviço não pode substituir o caminho; o
grupo do gateway pode atravessar o diretório e conectar, mas não remover o
socket. A instalação deve validar que usuários interativos não pertencem ao
grupo `haproxy`.

## Política por ambiente

- produção aceita somente `SISTER_LISTENER_MODE=systemd-unix` e o caminho
  canônico;
- `SISTER_BIND_HOST`, `SISTER_PORT`, argumento de porta e fallback TCP são
  proibidos em produção;
- desenvolvimento e teste usam TCP loopback por padrão e podem selecionar
  explicitamente o listener ativado para os testes de integração;
- falha do socket nunca abre `127.0.0.1:8000`;
- a saída `sisterd → Nexo/PostgreSQL` não é alterada por ISO-01.

## Ciclo de vida

`sisterd.socket` possui `RemoveOnStop=yes` e ativa uma única
`sisterd.service`. Reiniciar somente o processo preserva o inode, owner, grupo e
modo mantidos pela socket unit. Parar a socket unit remove o caminho. Arquivo
comum ou symlink no caminho não é removido silenciosamente pela aplicação,
porque ela nunca executa `bind()` em produção.

O rollback permitido restaura conjuntamente binário, service, socket unit,
tmpfiles e configuração anterior, com validação offline. É proibido recuperar
disponibilidade abrindo TCP, expondo `8000`, habilitando proxy legado ou
afrouxando permissões.

## Responsabilidades

- operação de plataforma mantém usuários, grupos, tmpfiles e unidades;
- operação do gateway garante associação exclusiva ao grupo autorizado;
- o `sisterd` apenas valida e consome o descritor herdado;
- HAProxy aponta para um único `unix@/run/sister/sisterd.sock` em produção;
- SEC-03V decide separadamente quais headers reconstruídos passam a ser
  confiáveis.

## Evidência e restrições

A prova reproduzida está em
[`ISO-01.md`](../evidence/security/ISO-01.md). Foram comprovados listener
ativado, ausência de TCP, falha fechada, reinício sobre o mesmo socket e
gateway real usando AF_UNIX.

O laboratório não possui as contas reais `sister`/`haproxy` nem executou a
unidade como PID 1; owner/grupo, `RemoveOnStop` e separação entre identidades
foram validados estruturalmente e por permissões simuladas. SELinux específico
e o E2E Nexo/PostgreSQL pertencem aos gates operacionais seguintes.

O controle não pretende bloquear `root`, processos executando sob uma identidade
autorizada, alteração privilegiada das unidades ou comprometimento do host.
Esses cenários permanecem riscos residuais explícitos.

ISO-01 não autoriza merge, tag, release ou exposição externa. O próximo gate é
SEC-03V.

## Consequências

- não existe listener TCP produtivo de entrada do `sisterd`;
- reinícios do processo não exigem que a aplicação recrie ou remova o socket;
- disponibilidade do gateway não pode ser recuperada por fallback inseguro;
- instalação passa a depender da existência validada dos usuários e grupos;
- ambientes de desenvolvimento conservam o fluxo TCP loopback explícito.
