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

O script sobe ou reutiliza o banco de teste, aplica migrations, compila o
`sisterd`, cria uma CA efêmera de sete dias, inicia o `sisterd` com socket
activation, renderiza o perfil `lan-lab` e valida o HAProxy antes de aceitá-lo.
Ele falha se o endereço não for um IPv4 privado ou se houver um processo
existente registrado pelo ciclo.

## Preparar outro computador

No computador cliente, adicione ao arquivo local de hosts:

```text
10.163.80.176 sister-gateway.test
```

Copie `.run/gateway/ca-lab.crt` para o cliente e instale-a como autoridade
certificadora de teste. Para uma verificação sem alterar o armazenamento do
navegador, use:

```bash
curl --cacert ca-lab.crt https://sister-gateway.test:8443/api/health
```

Depois, abra:

```text
https://sister-gateway.test:8443
```

O certificado precisa estar confiável no navegador. `curl -k` não é critério de
aceitação porque esconderia erro de identidade TLS.

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

## Diferença para produção

`lan-lab` é um perfil de teste de rede. Ele usa `SISTER_ENV=test`, certificado
efêmero e runtime no repositório. Produção usa `sisterd.socket`,
`/run/sister/sisterd.sock`, contas de serviço, certificado instalado em
`/etc/sister/gateway/tls.pem` e o preflight SEC-03V. Nenhuma alteração no
perfil `lan-lab` autoriza promoção ou exposição pública.
