# ADR-0019: Robustez HTTP e contenção interna de tentativas de login

## Status

Aceita — SEC-01C e SEC-01D na baseline `v0.2.6`

## Contexto

O parser convertia `Content-Length` pelo mesmo utilitário de configuração. Uma
entrada não numérica lançava exceção para fora do worker e podia encerrar o
processo. O limitador de login, por sua vez, usava `email@IP:porta`; uma nova
conexão TCP alterava a chave, e buckets antigos só eram podados quando a mesma
chave voltava a ser consultada.

O `sisterd` continua sendo um plano de controle interno, mas entradas inválidas
e abuso básico não podem comprometer sua disponibilidade.

A EFE-SisTer/1.2 relaciona esta decisão a `TH-HTTP-01`, `TH-HTTP-03`,
`TH-CXX-01`, `TH-CXX-02`, `TH-AUTH-01` e `TH-AUD-01`. A evidência reproduzível
está em `docs/evidence/security/SEC-01C-01D.md`; os riscos residuais devem ser
incorporados ao MAES-SisTer/1.0 depois da publicação da release.

## Decisão SEC-01C

`Content-Length` possui parser decimal dedicado e sem exceções, com três
resultados:

| Resultado | Resposta |
|---|---|
| decimal entre `0` e 16 MiB | processamento normal |
| vazio, sinal, caractere não decimal ou espaço interno | `400 Bad Request` |
| acima de 16 MiB ou overflow | `413 Payload Too Large` |

Cabeçalhos duplicados, inclusive `Content-Length`, são rejeitados com `400`. A
resposta usa mensagem de protocolo estável e não inclui exceção nem entrada do
cliente.

O pool de conexões contém `std::exception` e exceções desconhecidas na fronteira
de cada job. A conexão pertence ao pool, é fechada depois do handler mesmo sob
exceção, o evento é sanitizado e o worker continua consumindo a fila. Erros
esperados continuam tratados localmente; a barreira é somente a última defesa.

## Decisão SEC-01D

Cada tentativa sintaticamente válida de login é reservada atomicamente antes da
verificação da senha. Sucesso não apaga tentativas anteriores, evitando corrida
entre workers e diferença observável entre identidades existentes e ausentes.

Limites padrão em janela deslizante de cinco minutos:

| Escopo | Tentativas permitidas |
|---|---:|
| endereço IP observado | 32 |
| identidade normalizada | 16 |
| endereço IP + identidade | 8 |
| processo inteiro | 512 |

A identidade usa exatamente a normalização do `AuthStore`: remoção de espaço
externo e conversão para minúsculas. O endereço é o IPv4 observado no socket,
sem porta. `X-Forwarded-For` e cabeçalhos equivalentes não participam da decisão.

O armazenamento possui no máximo 4096 buckets. Toda tentativa poda buckets
expirados globalmente, sem depender de nova consulta à mesma chave. Se ainda
for necessário abrir espaço, o bucket não envolvido menos recentemente usado é
removido. Contadores monotônicos registram rejeições e remoções; uma rejeição
gera log operacional com escopo, quantidade de buckets e métricas, sem e-mail ou
senha.

Uma tentativa bloqueada recebe `429 Too Many Requests` e `Retry-After`, sem
indicar se a identidade existe.

## Invariantes

- Erro de protocolo conhecido não produz `5xx` nem atravessa o worker.
- Uma exceção inesperada não encerra o processo nem inutiliza o trabalhador.
- Alterar somente a porta TCP não cria novo bucket de endereço.
- Alterar e-mail não contorna o limite por endereço.
- Alterar endereço não contorna o limite por identidade.
- Contagem, poda e substituição são protegidas pelo mesmo mutex.
- O número de buckets nunca excede a capacidade configurada.
- O gateway futuro adiciona a primeira camada de contenção; não remove esta
  defesa interna.

## Riscos residuais

`SO_RCVTIMEO` e `SO_SNDTIMEO` são mantidos, mas não constituem defesa completa
contra Slowloris. SEC-03 deve atribuir ao gateway:

- prazo absoluto de headers e corpo;
- taxa mínima de transferência;
- limites de conexões simultâneas e por origem;
- normalização HTTP e confiança formalizada na origem do endereço do cliente.

O WebSocket legado não recebe investimento adicional: permanece desativado por
padrão e proibido em produção.

## Fora de escopo

- troca de `select()` por `poll()` ou `epoll()`;
- substituição geral do parser;
- streaming de uploads;
- logger assíncrono;
- reativação de proxies;
- gateway e contenção externa.
