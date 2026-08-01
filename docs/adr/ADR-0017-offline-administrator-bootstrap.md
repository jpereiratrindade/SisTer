# ADR-0017: Bootstrap administrativo local em produção

## Status

Aceita

## Contexto

Quando o repositório de identidades está vazio, o protótipo permite que o
primeiro cliente de `POST /api/auth/register` crie a conta administrativa. O
bind em loopback reduz a exposição direta, mas um gateway poderia publicar essa
janela durante uma instalação nova. A posse administrativa não pode depender de
quem alcança primeiro um endpoint HTTP.

## Decisão

O bootstrap administrativo HTTP fica desativado por padrão e é proibido em
produção. A configuração:

```text
SISTER_ENABLE_HTTP_BOOTSTRAP=false
```

é explícita na unidade systemd. Tentar habilitá-la com `SISTER_ENV=production`
causa falha de inicialização.

O primeiro administrador de produção é criado localmente, com senha lida de um
terminal sem eco:

```text
sisterctl auth bootstrap-admin <name> <email>
```

O comando usa `SISTER_AUTH_FILE`, preserva as validações do `AuthStore` e falha
quando o bootstrap já foi consumido. O arquivo de produção reside em
`/var/lib/sister/auth-users.tsv`, criado com acesso exclusivo pelo diretório de
estado do systemd.

Em desenvolvimento, o bootstrap HTTP permanece habilitado por padrão para
preservar o fluxo de laboratório. Ele pode ser desligado explicitamente.

## Invariantes

- Produção nunca aceita bootstrap administrativo por HTTP.
- `GET /api/auth/bootstrap` não anuncia janela aberta quando HTTP está desativado.
- `POST /api/auth/register` responde `403` quando HTTP está desativado.
- O comando local não aceita uma segunda criação administrativa de bootstrap.
- A senha não é recebida por argumento, ambiente ou saída do processo.
- O armazenamento continua protegido por permissões exclusivas.

## Consequências

- Uma instalação de produção requer uma etapa operacional local antes do login.
- O gateway pode publicar as rotas da aplicação sem abrir uma corrida pela
  primeira conta administrativa.
- Um futuro bootstrap remoto exigiria outro ADR e um segredo de instalação de
  alta entropia, curto, descartável e auditável.
