# ADR-CPP-01: Abstração eficiente e polimorfismo no núcleo C++

## Status

Aceita como política transversal para a materialização C++ do SisTer.

## Contexto

O `EXEC-01` precisa transformar o contrato de `IntegrationRun` em um modelo de
domínio seguro, testável e eficiente. Uma hierarquia de classes para cada estado
ou relação aumentaria acoplamento, propriedade indireta e superfície de erro,
sem benefício demonstrável para um conjunto de alternativas conhecido.

## Decisão

O núcleo do SisTer representará valores e invariantes com tipos finais de valor
e objetos encapsulados. A escolha de abstração obedecerá às seguintes regras:

- tipos identificadores, digests, referências e chaves terão semântica de valor;
- `IntegrationRun` será um agregado encapsulado, sem setters genéricos e com
  criação validada;
- estados e transições usarão `enum class`, funções puras e `std::expected`;
- alternativas fechadas usarão `std::variant`, sem hierarquia, RTTI ou downcast;
- variabilidade conhecida em compilação poderá usar `concepts` e templates;
- polimorfismo virtual ficará restrito a portas externas substituíveis em
  execução, como repositório, relógio, gerador de IDs e autorização;
- propriedade será explícita, preferindo valor e `std::unique_ptr`; `shared_ptr`
  exigirá compartilhamento real demonstrado;
- o domínio não dependerá de banco, HTTP ou formato JSON.

## Fluxo de fronteira

```text
JSON/DTO não confiável
    → validação de schema
    → validação semântica
    → fábrica do domínio
    → IntegrationRun válido
    → transição pura
    → porta de infraestrutura
```

DTOs de transporte não serão usados diretamente como objetos de domínio.

## Consequências

O desenho reduz estado inválido construível, torna transições testáveis e
concentra despacho dinâmico nas fronteiras onde a substituição de implementação
tem valor arquitetural. Não se promete custo zero absoluto: decisões de caminho
crítico devem ser confirmadas por teste ou benchmark.

São proibidos no modelo de estados: hierarquias `ProposedRun`/`RunningRun`,
herança para relações fechadas, downcast, RTTI para regra de negócio, estado
global mutável, setters arbitrários e exceções atravessando contratos sem tipo.

## Aplicação ao EXEC-01

`EXEC-01B` será o modelo de domínio encapsulado; `EXEC-01C`, máquinas de
execução e validade puras com tabela de transições verificável; `EXEC-01D`,
casos de uso e portas; `EXEC-01E`, persistência e serialização.

## Critérios de verificação

- nenhum `IntegrationRun` inválido pode ser construído publicamente;
- o contrato JSON e as invariantes C++ têm testes equivalentes;
- domínio e infraestrutura permanecem desacoplados;
- cada interface virtual possui fronteira e benefício de substituição
  documentados;
- alegações de desempenho relevantes possuem medição proporcional.
