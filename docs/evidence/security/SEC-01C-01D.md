# Evidência de segurança — SEC-01C e SEC-01D

**Data:** 1 de agosto de 2026  
**Base Git:** `87b6fc3e78edcb870141f80416be0d88777a81d7` (`v0.2.5`)  
**Release-alvo:** `v0.2.6`  
**Referência normativa:** EFE-SisTer/1.2  
**Revisão candidata:** worktree local; registrar o commit definitivo antes da publicação

## Rastreabilidade de ameaças

| Entrega | Ameaças EFE-SisTer/1.2 | Controles demonstrados |
|---|---|---|
| SEC-01C | `TH-HTTP-01`, `TH-HTTP-03`, `TH-CXX-01`, `TH-CXX-02` | parsing estrito e limitado, rejeição de framing inválido, barreira por job, fechamento da conexão e sobrevivência do processo |
| SEC-01D | `TH-AUTH-01`, `TH-HTTP-03`, `TH-AUD-01` | limites independentes e globais, memória limitada, decisão atômica, resposta uniforme, métricas e logs sem identidade |

O risco residual de requisições lentas e contenção na borda permanece atribuído
ao SEC-03. Esta evidência fecha apenas os controles declarados e não caracteriza
o `sisterd` como servidor HTTP público.

## Ambiente e comandos

- Linux `7.1.5-201.fc44.x86_64` x86_64;
- GCC `16.1.1`;
- CMake `4.3.0`;
- OpenSSL `3.5.7`.

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
./scripts/run_quality.sh
git diff --check
```

A validação com sanitizers usou build temporário separado, sem alterar o
worktree. AddressSanitizer foi executado com detecção de vazamentos e parada na
primeira falha.

O controle UndefinedBehaviorSanitizer foi **não executado** porque `libubsan`
está ausente no ambiente. O impacto é cobertura parcial de comportamento
indefinido; o tratamento é preparar um ambiente compatível. A tentativa não é
classificada como aprovação nem como falha da implementação.

## Casos executados

SEC-01C cobre:

- `Content-Length` alfabético, negativo, sinalizado, vazio e com espaço interno;
- overflow decimal e valores de 16 MiB e 16 MiB + 1;
- cabeçalho duplicado;
- sobrevivência e health check depois de cada requisição hostil;
- exceção `std::exception` e exceção desconhecida dentro de job;
- fechamento das conexões e continuidade do mesmo worker.

SEC-01D cobre:

- conexões sucessivas com novas portas de origem;
- troca de identidade preservando o endereço;
- troca de endereço preservando a identidade;
- limite combinado e limite global;
- `429` com `Retry-After`;
- 5000 combinações sob capacidade máxima de 64 buckets no teste;
- poda global após expiração;
- 200 tentativas concorrentes com resultado determinístico de 100 permissões e
  100 rejeições no limite configurado pelo teste.

## Resultado

- Testes direcionados de unidade e integração: aprovados.
- Pipeline integral: 12/12 testes CTest aprovados; contratos, governança,
  recursos locais, maturidade, subsistemas, SGE e shell aprovados.
- Build com `-Wall -Wextra -Wpedantic`: aprovado.
- AddressSanitizer: 2/2 testes de hardening aprovados, sem erro ou vazamento.
- UndefinedBehaviorSanitizer: indisponível por ausência da biblioteca de runtime.
- Processo após requisições hostis: permaneceu ativo e saudável.
- Respostas a erros do cliente: `400`, `413` ou `429`, sem `5xx`.
- Logs de bloqueio: contêm somente escopo e contadores; não contêm identidade,
  senha ou corpo da requisição.
- Falhas conhecidas na execução direcionada: nenhuma.
