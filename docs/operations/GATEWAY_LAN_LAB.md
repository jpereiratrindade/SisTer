# Teste do gateway pela rede local

Este procedimento permite acessar o SisTer de outro equipamento da mesma rede
com o mesmo desenho de transporte usado em produção: o HAProxy é a única
fronteira TCP e encaminha para o `sisterd` por socket Unix.

```text
cliente -> https://sister-gateway.test:8443
             -> HAProxy no IPv4 privado do laptop
             -> .run/gateway/sisterd.sock
             -> sisterd em SISTER_ENV=test
```

## Pré-requisitos

No laptop:

- banco de teste disponível via Podman;
- `GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22`;
- endereço IPv4 privado da interface que deve receber conexões, por exemplo
  `10.163.80.176`;
- firewall permitindo TCP `8443` somente na rede de teste.

O `sisterd` não escuta em `8000` nem `8001` neste fluxo. O endereço privado
precisa ser informado explicitamente para evitar que o serviço seja publicado
acidentalmente em todas as interfaces.

## Iniciar

```bash
export GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22
export GATEWAY_LAN_ADDRESS=10.163.80.176
./scripts/run_gateway_lan_lab.sh
```

Para executar ecossistema governado completo, use perfil canônico:

```bash
export GATEWAY_HAPROXY_BIN=/usr/local/sbin/haproxy-3.2.22
export GATEWAY_LAN_ADDRESS=10.163.80.176
./scripts/run_all.sh --profile dev-lan
```

Nesse perfil, `run_all.sh` registra ownership da execução, mantém núcleo em
socket Unix e declara `LAN_FEDERATED`. `dev-reference` permanece local e nunca
publica `8443`.

O script sobe ou reutiliza o banco de teste, aplica migrations, compila o
`sisterd`, cria uma CA efêmera de sete dias, inicia o `sisterd` com socket
activation, renderiza o perfil `lan-lab` e valida o HAProxy antes de aceitá-lo.
Ele falha se o endereço não for um IPv4 privado ou se houver um processo
existente registrado pelo ciclo.

## Criar o usuário de teste

O `lan-lab` desativa o cadastro administrativo pela página. Isso é intencional:
o acesso inicial deve ser criado no terminal, como em produção. Faça isso antes
de iniciar o gateway pela primeira vez:

```bash
./scripts/bootstrap_gateway_lan_admin.sh \
  "Administrador LAN" admin@example.org
```

Digite a mesma senha nas duas perguntas. A senha não aparece no terminal nem
fica na linha de comando. Depois inicie o gateway:

```bash
./scripts/run_gateway_lan_lab.sh
```

Na página `/login`, use exatamente o e-mail e a senha criados acima. O arquivo
usado pelo processo é `.run/gateway/auth-users.tsv`; uma conta existente no
ambiente `dev` não é compartilhada automaticamente com o `lan-lab`.

Se o gateway já estiver rodando, pare-o antes do bootstrap:

```bash
./scripts/stop_gateway_lan_lab.sh
```

O comando de bootstrap aceita uma única conta inicial. Depois do primeiro login,
use a área administrativa **Equipe** para cadastrar outras contas.

## Acessar no mesmo laptop

O comando de inicialização não altera `/etc/hosts` nem o armazenamento de
certificados automaticamente. No próprio laptop, execute:

```bash
grep -qE '[[:space:]]sister-gateway\.test([[:space:]]|$)' /etc/hosts || \
  echo '10.163.80.176 sister-gateway.test' | sudo tee -a /etc/hosts

sudo cp .run/gateway/ca-lab.crt \
  /etc/pki/ca-trust/source/anchors/sister-gateway-lab-ca.crt
sudo update-ca-trust
```

Não use `/tmp/ca-lab.crt` neste caso. Esse caminho só é usado quando a CA foi
copiada para outro computador.

Confirme antes do navegador:

```bash
getent hosts sister-gateway.test
NO_PROXY=sister-gateway.test,10.163.80.176 \
no_proxy=sister-gateway.test,10.163.80.176 \
curl --noproxy '*' https://sister-gateway.test:8443/api/health
```

Se aparecer `CONNECT tunnel failed` ou resposta `503` do proxy, a requisição
ainda está passando pelo proxy da máquina. Configure `sister-gateway.test` e
`10.163.80.176` na lista de exceções do proxy do sistema ou do navegador. A
URL local não deve passar por proxy.

Abra exatamente:

```text
https://sister-gateway.test:8443
```

## Acessar de outro computador Fedora

Esta seção só se aplica a outro computador. Não execute estes comandos no
laptop servidor. Execute os comandos seguintes no laptop SisTer para copiar a
CA e o diagnóstico para o computador cliente. Substitua `usuario` e
`IP_DO_CLIENTE` pelos valores reais:

```bash
scp .run/gateway/ca-lab.crt usuario@IP_DO_CLIENTE:/tmp/
scp scripts/check_gateway_lan_access.sh usuario@IP_DO_CLIENTE:/tmp/
```

No computador cliente, execute:

```bash
echo '10.163.80.176 sister-gateway.test' | sudo tee -a /etc/hosts
sudo cp /tmp/ca-lab.crt \
  /etc/pki/ca-trust/source/anchors/sister-gateway-lab-ca.crt
sudo update-ca-trust

chmod +x /tmp/check_gateway_lan_access.sh
/tmp/check_gateway_lan_access.sh 10.163.80.176 /tmp/ca-lab.crt
```

O diagnóstico testa, nesta ordem, nome local, porta TCP, certificado TLS e
resposta da aplicação. Só abra o navegador depois de obter `OK: acesso ao
SisTer funcionando`:

```text
https://sister-gateway.test:8443
```

Não use `localhost`, `127.0.0.1`, o IP diretamente ou `curl -k`. O gateway exige
o nome exato para validar SNI, Host e certificado.

Se o computador cliente não for Fedora, mantenha a entrada em hosts e instale
`.run/gateway/ca-lab.crt` no armazenamento de autoridades certificadoras do
sistema ou do navegador.

## Verificar e parar

No laptop:

```bash
ss -ltn '( sport = :8000 or sport = :8001 or sport = :8443 )'
curl --resolve sister-gateway.test:8443:10.163.80.176 \
  --cacert .run/gateway/ca-lab.crt \
  https://sister-gateway.test:8443/api/health
./scripts/stop_gateway_lan_lab.sh
```

O único listener TCP esperado durante o fluxo é `10.163.80.176:8443`. O
upstream permanece em `.run/gateway/sisterd.sock` e os PIDs/logs ficam no mesmo
diretório privado.

Quando o gateway foi iniciado por `run_all.sh --profile dev-lan`, o comando de
parada delega ao manifesto da execução ativa. Assim, encerra gateway, núcleo e
subsistemas iniciados por aquela execução, enquanto preserva contêineres e
demais recursos que já existiam antes dela. Sem uma execução `dev-lan` ativa,
o comando limita-se aos processos registrados em `.run/gateway`.

## Diferença para produção

`lan-lab` é um perfil de teste de rede. Ele usa `SISTER_ENV=test`, certificado
efêmero e runtime no repositório. Produção usa `sisterd.socket`,
`/run/sister/sisterd.sock`, contas de serviço, certificado instalado em
`/etc/sister/gateway/tls.pem` e o preflight SEC-03V. Nenhuma alteração no
perfil `lan-lab` autoriza promoção ou exposição pública.
