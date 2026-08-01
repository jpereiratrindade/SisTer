# ADR-0015: Quarentena de transporte do sisterd

## Status

Aceita — SEC-00 concluído na baseline `v0.2.5`

## Contexto

O `sisterd` reúne temporariamente parser e servidor HTTP próprios, arquivos
estáticos, autenticação, APIs e proxies HTTP/WebSocket para subsistemas. No
túnel WebSocket legado, cada conexão persistente ocupa um trabalhador do mesmo
pool usado pelo plano de controle. Essa composição foi útil para validar o
protótipo, mas não constitui uma borda de rede adequada para produção.

A EFE-SisTer/1.1 definiu o `sisterd` como plano de controle persistente e exigiu
uma decisão explícita sobre manter, endurecer ou substituir o servidor HTTP. A
EFE-SisTer/1.2, referência corrente, preserva essa fronteira e acrescenta o
perfil restrito de transporte e a engenharia orientada por ameaças.
O plano de transição já atribui TLS, HTTP, WebSocket, limites e observabilidade
de transporte a um gateway especializado.

## Decisão

O `sisterd` fica em quarentena de transporte:

1. Em produção, aceita somente bind IPv4 em loopback (`127.0.0.0/8`).
2. Um gateway especializado é a única borda de rede autorizada e deve terminar
   TLS e aplicar limites, timeouts e observabilidade de transporte.
3. Os proxies HTTP e WebSocket existentes são mecanismos legados de laboratório.
4. Em produção, `SISTER_ENABLE_LEGACY_PROXY` e
   `SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY` devem permanecer `false`; habilitá-los
   causa falha de inicialização.
5. Em desenvolvimento, os mecanismos legados só podem ser usados de forma
   explícita nos processos e testes que ainda caracterizam o protótipo.
6. Nenhuma nova integração pode adicionar proxy específico ao `main.cpp`.

Configuração mínima de produção:

```text
SISTER_ENV=production
SISTER_BIND_HOST=127.0.0.1
SISTER_ENABLE_LEGACY_PROXY=false
SISTER_ENABLE_LEGACY_WEBSOCKET_PROXY=false
```

## Invariantes

- A porta do `sisterd` não é publicada diretamente em uma interface de rede.
- Somente o gateway alcança o listener interno em produção.
- TLS cobre todas as páginas e APIs no gateway.
- WebSockets de usuários não ocupam trabalhadores do `sisterd` em produção.
- O cookie de sessão do SisTer não deve atravessar a fronteira para subsistemas
  no caminho arquitetural definitivo.
- A autorização de cada integração deve ocorrer antes do encaminhamento.

## Consequências

- Uma configuração de produção insegura falha antes do `bind()`.
- O acesso integrado de Clima e Nexo depende da configuração do gateway; o
  proxy embarcado deixa de ser fallback de produção.
- O fluxo legado continua disponível em desenvolvimento enquanto a migração é
  testada, mas permanece inelegível para promoção.
- Socket Unix com permissões restritas é a evolução preferencial do listener
  interno e requer implementação posterior.
- Identidade interna assinada, autorização por capacidades e contenção de abuso
  permanecem entregas de segurança separadas e obrigatórias.

A autorização por capacidades foi concluída em SEC-01. Identidade interna
assinada e contenção de abuso permanecem fora do escopo desta decisão.
