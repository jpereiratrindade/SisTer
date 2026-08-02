# HAPROXY-RPM-01 — pacote local do laboratório SEC-03V

Este diretório contém a receita e os metadados versionados para produzir
`sister-haproxy-lab-3.2.22`. O RPM instala somente o ELF nativo em
`/usr/local/sbin/haproxy-3.2.22` e documentação. Ele não instala configuração,
usuário, listener, wrapper, container ou unidade systemd genérica.

O pacote não é oficial do HAProxy nem do Fedora. Sua autoridade é restrita ao
laboratório candidato SEC-03V e depende de revisão da fonte, build isolado,
assinatura dedicada e manifesto de proveniência.

Fingerprint da chave pública governada:

```text
ED3F 4CE4 C756 983F 2110 97B6 AB5D 893C 71F3 1D65
```

A chave pública está em `keys/sister-sec03v-rpm-signing.asc`. A chave privada e
a passphrase permanecem exclusivamente no keyring ignorado em `.run`.

## Host de destino

O host confirmado é Fedora 44 Workstation. A instalação final usa uma transação
DNF com RPM local; `rpm-ostree` não se aplica a este host.

## Fonte congelada

```text
URL: https://www.haproxy.org/download/3.2/src/haproxy-3.2.22.tar.gz
SHA-256: afca3a26d573df53d0e1fc475dcd743ec5875e038e1476c80e871d70228ca2da
```

Baixar novamente e verificar:

```bash
./scripts/packaging/prepare_haproxy_source.sh
```

O tarball permanece em `.run/packaging/haproxy/sources` e não entra no Git.

## Ferramentas operacionais

Instalar pelo gerenciador do Fedora antes do build:

```bash
sudo dnf install rpm-build rpm-sign podman
```

O build validado neste host usa a imagem oficial Fedora 44 em Podman. O
container recebe apenas o SRPM e um diretório novo de resultados; nenhuma chave
é montada nele. Podman é ferramenta de build, não runtime do gateway candidato.

## SRPM e build isolado

```bash
./scripts/packaging/build_haproxy_rpm.sh
```

O build produz SRPM, RPM binário, inventário de dependências, log e identidade
da imagem em `.run/packaging/haproxy/podman-results/<UTC>`, sem acessar a chave
de assinatura. O acesso de rede serve apenas à resolução das dependências de
build do Fedora; o tarball já está congelado pelo SHA-256 oficial.

O HAProxy 3.2 implementa `sd_notify` internamente. Por isso `-Ws` é testado, mas
`USE_SYSTEMD` e `systemd-devel` não fazem parte da receita.

## Chave dedicada e assinatura

Criar uma chave exclusiva, com passphrase, em um keyring ignorado pelo Git:

```bash
signing_home="$PWD/.run/packaging/haproxy/gnupg"
install -d -m 0700 "$signing_home"
GNUPGHOME="$signing_home" gpg --quick-generate-key \
  "SisTer SEC-03V Lab RPM Signing" rsa3072 sign 1y
GNUPGHOME="$signing_home" gpg --armor --export \
  "SisTer SEC-03V Lab RPM Signing" \
  > "$PWD/.run/packaging/haproxy/sister-sec03v-rpm-signing.asc"
chmod 0600 "$PWD/.run/packaging/haproxy/sister-sec03v-rpm-signing.asc"
```

Não informar a passphrase em argumentos, variáveis, arquivos do repositório ou
chat. O fingerprint público deve ser revisado antes de assinar. Depois de
instalar `rpm-sign`, executar:

```bash
export GNUPGHOME="$PWD/.run/packaging/haproxy/gnupg"
export HAPROXY_SIGNING_FINGERPRINT="<FINGERPRINT COMPLETO REVISADO>"
./scripts/packaging/sign_haproxy_rpms.sh \
  .run/packaging/haproxy/podman-results/<UTC>/*.src.rpm \
  .run/packaging/haproxy/podman-results/<UTC>/*.x86_64.rpm
```

O script recusa identificadores curtos, exporta apenas a chave pública e valida
as assinaturas em um banco RPM temporário. Em seguida, gerar o manifesto com
o spec já commitado:

```bash
result_dir="$PWD/.run/packaging/haproxy/podman-results/<UTC>"
python3 scripts/packaging/generate_haproxy_provenance.py \
  --srpm "$(find "$result_dir" -name '*.src.rpm' -print -quit)" \
  --rpm "$(find "$result_dir" -name '*.x86_64.rpm' -print -quit)" \
  --public-key packaging/haproxy/keys/sister-sec03v-rpm-signing.asc \
  --fingerprint "$HAPROXY_SIGNING_FINGERPRINT" \
  --build-environment "$result_dir/build-environment.txt" \
  --output docs/evidence/security/HAPROXY-RPM-01.json
```

## Verificações obrigatórias

Para cada pacote:

```bash
rpm -Kv pacote.rpm
rpm -qpi pacote.rpm
rpm -qpl pacote.rpm
rpm -qpR pacote.rpm
sha256sum pacote.rpm
```

O RPM binário deve listar somente:

```text
/usr/local/sbin/haproxy-3.2.22
licenças e documentação RPM
```

`rpm -qp --scripts` não deve apresentar scripts de instalação. A assinatura e
os hashes finais devem ser registrados no manifesto gerado após o build.

## Instalação no Workstation

Somente após revisão do manifesto e da chave pública:

```bash
public_key="$PWD/packaging/haproxy/keys/sister-sec03v-rpm-signing.asc"
package="$PWD/.run/packaging/haproxy/podman-results/<UTC>/sister-haproxy-lab-3.2.22-1.sistersec03v.fc44.x86_64.rpm"

gpg --show-keys --with-fingerprint "$public_key"
sudo rpmkeys --import "$public_key"
rpmkeys --checksig --verbose "$package"
sudo dnf --setopt=localpkg_gpgcheck=1 install "$package"
```

Registrar o ID da transação apresentado por `dnf history`. O rollback permitido
é `sudo dnf history undo <ID>`, seguido das verificações de ausência do binário
e estado das unidades. Após remover o único pacote que confia nessa chave, a
chave pública pode ser retirada com `sudo rpmkeys --delete <FINGERPRINT>`.
Não iniciar `sister-gateway.service` nesta fase; isso pertence a
SEC-03V-ENV-B.
