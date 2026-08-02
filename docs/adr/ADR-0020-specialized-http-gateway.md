# ADR-0020: Gateway especializado e fronteira HTTP externa

## Status

Aceita para SEC-03A — perfil definido; implantação bloqueada até SEC-03B/C/V

## Contexto

O `sisterd` é um plano de controle interno e permanece em loopback. SEC-00
retirou o processo da borda, SEC-01C/01D endureceu seu parser e o login, e
SEC-02 publicou somente uma leitura interna assinada do Nexo. Esses controles
não transformam o parser próprio do `sisterd` em uma borda HTTP generalista.

SEC-03 deve atribuir a um componente especializado TLS, normalização HTTP,
limites, contenção de clientes lentos, saneamento de headers e correlação. A
fronteira trata `TH-HTTP-02/03/04`, `TH-WS-01`, `TH-PROXY-01/02`,
`TH-CONF-01` e `TH-AUD-01` sem absorver autorização ou domínio.

## Decisão de produto

Adotar **HAProxy Community 3.2 LTS**, inicialmente na versão **3.2.22 ou patch
posterior da mesma linha 3.2**, instalado como pacote do sistema e operado por
`systemd`. A linha 3.2 é LTS até 2030-Q2; o patch mínimo acompanha correções de
segurança e deve aumentar quando a linha publicar atualização. Troca para 3.4
LTS ou outra linha exige requalificação do perfil e SEC-03V, não apenas mudança
de pacote.

A escolha se baseia em garantias necessárias à fronteira:

- parser e modo HTTP próprios, limites globais e por conexão;
- `timeout http-request` absoluto, independente de atividade parcial;
- remoção e reconstrução de headers antes do upstream;
- geração de identificador único e logs correlacionados;
- ACLs, destinos estáticos, stick tables e limitação de taxa;
- validação de configuração offline e reload controlado;
- queda de privilégios e operação sem control plane.

Envoy atende ao perfil, mas adicionaria nesta fase API de configuração e modelo
operacional mais amplos que o único upstream fixo requer. NGINX e Caddy não são
adotados neste gate porque a combinação de taxa multidimensional, prazo
absoluto e validação executável exigiria módulos ou mecanismos adicionais. A
decisão pode ser revista por nova ADR acompanhada dos mesmos testes negativos.

Referências oficiais consultadas em 1 de agosto de 2026:

- [ciclo e suporte das versões HAProxy](https://www.haproxy.org/);
- [manual de configuração HAProxy 3.2](https://docs.haproxy.org/3.2/configuration.html);
- [guia de gestão HAProxy 3.2](https://docs.haproxy.org/3.2/management.html).

## Fronteira e responsabilidades

```text
cliente não confiável
        │ TLS 1.3 / HTTPS :443
        ▼
HAProxy (usuário sister-gateway)
  ├── Host allowlist e HTTP estrito
  ├── limites, deadlines e rate limiting
  ├── remove origem, identidade e correlação externas
  ├── cria request_id e headers autorizados
  └── destino fixo, sem descoberta dinâmica
        │ HTTP/1.1 / 127.0.0.1:8000
        ▼
sisterd (usuário sister)
  ├── autenticação e autorização funcional
  ├── regras de domínio e maturidade
  └── emissão da identidade assinada interna
        │ política SEC-02 exata
        ▼
Nexo
```

O gateway não autentica usuários, não decide capacidades, não emite
`Sister-Assertion`, não lê a chave privada de identidade interna, não acessa
Nexo, não administra acordos e não persiste dados do SisTer.

## Instalação, propriedade e atualização

- Binário proveniente de repositório de sistema ou fornecedor aprovado, com
  assinatura verificada; imagens ou plugins de terceiros não integram a
  baseline inicial.
- Processo dedicado `sister-gateway`; configuração e certificados pertencem a
  `root:sister-gateway`. Arquivos com chave privada usam no máximo `0640` e
  diretórios, `0750`.
- O `sisterd` continua sob o usuário `sister`. Sua chave Ed25519 não pertence ao
  grupo do gateway.
- Configuração candidata passa por validação offline, testes de laboratório e
  reload. Atualização de patch é aplicada primeiro em laboratório; advisories
  críticos podem abreviar a janela, mas não dispensam validação sintática e
  smoke test.
- Acesso ao upstream de loopback é restringido no host ao usuário/cgroup do
  gateway. Loopback isoladamente não satisfaz esse controle.

## TLS, hosts e protocolos

- Porta externa única: `443/tcp`. A porta `80/tcp` permanece fechada na
  primeira baseline, sem redirect implícito.
- TLS mínimo e máximo `1.3`; certificado emitido por CA aprovada para o host
  exato. Certificado inválido, ausente ou expirado impede promoção.
- Renovação prepara novo PEM, valida chave/cadeia/host, testa a configuração e
  faz reload. O PEM anterior fica disponível para rollback pelo período
  operacional aprovado.
- HSTS permanece desligado até um gate de implantação confirmar domínio,
  subdomínios, renovação e rollback sustentáveis.
- Downstream inicial aceita somente HTTP/1.1. HTTP/2, HTTP/3, `Upgrade` e
  WebSocket permanecem desabilitados.
- `Host` usa allowlist exata, sem wildcard. Host ausente, duplicado ou
  desconhecido é rejeitado antes do upstream.

## Headers e correlação

Antes de reconstruir a requisição, o gateway remove todas as ocorrências de:

```text
X-Sister-*
X-Forwarded-For
X-Forwarded-Host
X-Forwarded-Proto
X-Request-ID
Forwarded
```

Reconstrói somente `X-Forwarded-For` a partir do endereço observado,
`X-Forwarded-Host` a partir do host canônico, `X-Forwarded-Proto=https` e um
novo `X-Request-ID`. O ID tem 32 caracteres hexadecimais minúsculos e nunca usa
valor do cliente. O `sisterd` só poderá confiar nesse ID depois que SEC-03B
implementar e provar a restrição do upstream; até lá, continua gerando o seu.
SEC-03V deve demonstrar uma única correlação gateway–`sisterd`–Nexo–PostgreSQL.

`Cookie` é encaminhado apenas ao `sisterd`, onde representa a sessão humana.
Ele nunca é encaminhado pelo cliente Nexo, conforme SEC-02.

## Limites e contenção

O perfil normativo em
[`GATEWAY_SECURITY_PROFILE.md`](../security/GATEWAY_SECURITY_PROFILE.md) fixa
valores iniciais e o artefato executável. Entre os invariantes:

- apenas `GET`, `HEAD`, `POST`, `PUT`, `PATCH` e `DELETE`;
- alvo até 8 KiB, no máximo 64 headers e 16 KiB agregados de headers;
- corpo global até 1 MiB, com limite de 64 KiB para autenticação;
- `Content-Length` duplicado, `Transfer-Encoding` não permitido ou a presença
  simultânea dos dois são rejeitados;
- prazo absoluto de 5 s para headers e 10 s para corpo; conexão, fila, cliente,
  servidor e keep-alive possuem timeouts explícitos; taxa recebida abaixo de
  1 KiB/s é encerrada;
- limites global, por origem, por rota e específico para login;
- resposta upstream acima de 16 MiB é interrompida e registrada sem conteúdo.

O limitador interno do `sisterd` permanece como defesa em profundidade. O
gateway não converte `X-Forwarded-For` em autoridade funcional.

## Logs e observabilidade

Logs estruturados registram timestamp, evento, resultado, origem observada,
host canônico, método, rota sem query sensível, status, duração, bytes,
`request_id` e regra de bloqueio. Não registram cookies, autorização, corpo,
query completa, asserções, chaves ou cabeçalhos `X-Sister-*`. Métricas distinguem
TLS, protocolo, Host, tamanho, deadline, taxa, fila e falha upstream.

## Rollback e falha fechada

Cada promoção preserva pacote, configuração, certificado e unidade anteriores.
Rollback restaura o conjunto anterior de forma atômica, valida offline, recarrega
o gateway e executa health pelo caminho externo. Se isso falhar, `443` fica
indisponível: o procedimento nunca muda o bind do `sisterd`, habilita proxy
legado, abre `8000` externamente ou reduz TLS/limites.

## Gates

- **SEC-03A:** ADR, perfil, esquema, validador e matriz de ameaças.
- **SEC-03B:** configuração HAProxy mínima em laboratório, TLS, Host, headers,
  ID, limites e logs.
- **SEC-03C:** deadlines, conexões, rate limiting e métricas de abuso.
- **SEC-03V:** matriz negativa, integração Nexo, evidência e decisão de risco.

Nenhuma release ou exposição externa é autorizada por esta ADR isoladamente.
A `v0.2.8` só pode ser considerada depois de SEC-03V. SEC-02R continua
obrigatório antes de qualquer escrita, e WebSocket requer decisão e gate próprios.

## Consequências

- A fronteira de transporte passa a ter owner e requisitos verificáveis.
- O `sisterd` continua servindo interface e API nesta primeira arquitetura.
- A implantação acrescentará um componente e um procedimento de certificados,
  atualização e rollback.
- Falha do gateway causa indisponibilidade externa, não retorno ao transporte
  inseguro.
