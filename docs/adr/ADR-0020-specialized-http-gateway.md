# ADR-0020: Gateway especializado e fronteira HTTP externa

## Status

Aceita — ISO-01 e SEC-03V comprovados no laboratório candidato; promoção governada pendente

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

Adotar **HAProxy Community 3.2 LTS**, instalado como pacote do sistema e operado
por `systemd`. A linha permitida é **3.2.x**, o piso inicial validado é
**3.2.22** e a política exige o patch mantido mais recente disponível nessa
linha, nunca abaixo do piso. A linha 3.2 é LTS até 2030-Q2. Troca para 3.4 LTS
ou outra linha exige requalificação do perfil e SEC-03V, não apenas mudança de
pacote.

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
- [RFC 9112 — HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html).

Na data da decisão, o índice e o manual oficiais já identificam `3.2.22`. Uma
referência anterior a `3.2.21` é um snapshot ultrapassado e não reduz o piso.

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
        │ HTTP/1.1 / unix@/run/sister/sisterd.sock
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
- Acesso ao upstream usa o socket Unix governado pela ADR-0021; loopback TCP é
  proibido em produção.

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
- `Host` usa allowlist exata, sem wildcard. Host ausente, desconhecido,
  divergente, com porta inesperada ou em absolute-form é rejeitado. Duplicação
  idêntica segue exclusivamente a exceção SEC-03B-R e chega canônica ao upstream.

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
valor do cliente. O `sisterd` só poderá confiar nesse ID depois que um gate
posterior implementar e provar o isolamento local do upstream; até lá, continua
gerando o seu.
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
- `Content-Length` válido e idêntico pode ser normalizado para um único valor;
  valores inválidos ou divergentes, `Transfer-Encoding` e a presença simultânea
  de ambos são rejeitados;
- prazo absoluto de 5 s para headers e alvo de 10 s para corpo; conexão, fila,
  cliente, servidor e keep-alive possuem timeouts explícitos;
- limites global, por origem, por rota e específico para login;
- alvo de taxa mínima recebida de 1 KiB/s e de resposta upstream máxima de
  16 MiB, ambos ainda `MECHANISM_UNPROVEN` e sem artifícios de extensão.

## Gate de realizabilidade

SEC-03A define requisitos, não presume que toda garantia possui uma diretiva
HAProxy direta. SEC-03B começa pela seguinte matriz:

| Requisito | Mecanismo candidato | Estado antes do laboratório |
|---|---|---|
| TLS 1.3 | controles TLS de `bind` | `NATIVE_DOCUMENTED` |
| HTTP/1.1 único | ALPN e protocolos de `bind` | `LAB_PROOF_REQUIRED` |
| deadline absoluto de headers | `timeout http-request` | `NATIVE_DOCUMENTED` |
| limite de headers | `tune.http.maxhdr` e buffers | `LAB_PROOF_REQUIRED` |
| corpo de 1 MiB | ACL de `Content-Length` e testes reais | `LAB_PROOF_REQUIRED` |
| taxa mínima de 1 KiB/s | mecanismo ainda não aceito | `MECHANISM_UNPROVEN` |
| resposta até 16 MiB | mecanismo ainda não aceito | `MECHANISM_UNPROVEN` |
| request ID com 32 hex | `unique-id-format` e `unique-id-header` | `LAB_PROOF_REQUIRED` |
| remoção de `X-Sister-*` | regras de remoção de headers | `LAB_PROOF_REQUIRED` |
| rate limiting | stick tables e contadores | `PROVEN` em SEC-03C |

Lua, plugins e módulos de terceiros permanecem proibidos. Se um requisito não
puder ser realizado nativamente e de forma simples, o laboratório registra a
limitação, realoca o controle ou mantém o risco residual; não cria extensão
apenas para tornar o perfil aparentemente conforme.

O limitador interno do `sisterd` permanece como defesa em profundidade. O
gateway não converte `X-Forwarded-For` em autoridade funcional.

## Resolução SEC-03B-R

O laboratório encerrou SEC-03B como `LAB_PROVEN_WITH_RESTRICTIONS`. A
normalização segura de `Content-Length` idêntico é aceita conforme RFC 9112;
campos isolados de Upgrade são removidos e o handshake completo é rejeitado.

O RFC 9112 exige `400` para múltiplas linhas Host. HAProxy 3.2.22 normaliza
linhas idênticas antes das ACLs, portanto esse caso é
`ACCEPTED_LAB_DIVERGENCE`, não conformidade literal. A aceitação depende de SNI
estrito, Host e porta exatos, absolute-form recusado, upstream literal e Host
canônico reconstruído. O owner é `gateway and transport maintainers`; SEC-03V
revisa o risco. Qualquer expansão para múltiplas autoridades ou destinos reabre
SEC-03B.

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
- **SEC-03B:** concluído no laboratório com a resolução SEC-03B-R e exceção de
  Host restrita.
- **SEC-03C:** concluído em laboratório com limites, falhas controladas e logs
  sanitizados; deadline absoluto do corpo permanece parcial.
- **ISO-01:** concluído com socket Unix ativado e permissões governadas;
  identidades reais e ciclo PID 1 permanecem para o ambiente candidato.
- **SEC-03V:** matriz negativa, composição gateway/Nexo/PostgreSQL, revisão da
  exceção de Host, evidência e decisão de risco — concluído no candidato,
  conforme [`SEC-03V.md`](../evidence/security/SEC-03V.md).

Nenhuma release ou exposição externa é autorizada por esta ADR isoladamente.
A `v0.2.8` pode ser considerada após revisão da evidência e promoção governada.
SEC-02R continua obrigatório antes de qualquer escrita, e WebSocket requer
decisão e gate próprios.

## Consequências

- A fronteira de transporte passa a ter owner e requisitos verificáveis.
- O `sisterd` continua servindo interface e API nesta primeira arquitetura.
- A implantação acrescentará um componente e um procedimento de certificados,
  atualização e rollback.
- Falha do gateway causa indisponibilidade externa, não retorno ao transporte
  inseguro.
