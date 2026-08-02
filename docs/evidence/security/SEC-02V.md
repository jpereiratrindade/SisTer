# Evidência de segurança — SEC-02V

**Data:** 1 de agosto de 2026

**Baseline:** `v0.2.6` (`da965b17532add5a7b1a5da462285af121b7bc8d`)

**SisTer — implementação:** `d2d43fe` — identidade assinada e cliente Nexo

**SisTer — testes:** `5634050` — emissor, sanitização e ponta a ponta

**Nexo — implementação:** `490676b` — verificador e política assinada

**Nexo — testes:** `9ef64c6` — matriz negativa, rotação e reinício

**Nexo — documentação:** `12f0f72`

**Referências:** EFE-SisTer/1.2, MAES-SisTer/1.0, ADR-0018 e ADR-0007 do Nexo

## Ambiente

- Linux `7.1.5-201.fc44.x86_64` x86_64;
- GCC `16.1.1`;
- CMake `4.3.0`;
- OpenSSL `3.5.7`;
- PostgreSQL 17 em contêiner local saudável;
- listeners de teste restritos a `127.0.0.1`.

As chaves Ed25519 utilizadas pertencem exclusivamente a fixtures de teste. A
evidência não contém chave privada, asserção completa, cookie, token de sessão
ou credencial do banco.

## Comandos e resultados

```bash
# SisTer
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
./scripts/run_quality.sh

# Nexo
cmake -S . -B build -DNEXO_BUILD_TESTS=ON
cmake --build build
ctest --test-dir build --output-on-failure

# processos reais
python3 tests/sec02v_http_test.py <nexo> <web> <database-url>
python3 tests/sec02v_sisterd_nexo_e2e.py \
  <sisterd> <sister-web> <nexo> <nexo-web> <database-url>
```

Resultados:

- SisTer: 12/12 testes CTest aprovados;
- Nexo: 2/2 testes CTest aprovados;
- matriz HTTP assinada: aprovada;
- teste ponta a ponta `sisterd` → Nexo → PostgreSQL: aprovado;
- contratos, governança, maturidade, SGE e shell do SisTer: aprovados;
- warnings `-Wall -Wextra -Wpedantic`: nenhum na revisão final;
- identidades transitórias criadas pelos testes: removidas do banco local.

## Bloco A — emissão pelo `sisterd`

Foi comprovado que a asserção contém:

- `iss=sisterd` e sujeito derivado da sessão autorizada;
- `aud=sister_nexo`;
- somente `nexo.projects.read`;
- `purpose=research_operations`;
- `iat`, `exp`, `jti` aleatório e `request_id` interno;
- TTL configurável entre 1 e 300 segundos.

O cliente específico cria a requisição do zero. Cookie, autorização externa,
`X-Sister-*` e `X-Request-ID` externos não são encaminhados. O caminho externo
`/integrations/nexo/projects` é traduzido para a política real
`/api/v1/projects`.

## Bloco B — criptografia e chaves

- algoritmo protegido fixo `EdDSA` e tipo `sister-internal+jwt`;
- chave privada Ed25519 em caminho absoluto e com modo `0600` ou mais restrito;
- configuração ausente ou permissiva impede a conexão ao Nexo;
- chave pública inválida e `kid` desconhecido falham fechados;
- nenhum material criptográfico ou asserção completa apareceu nos logs.

## Bloco C — validação no Nexo

Foram rejeitados antes da regra de domínio, com resposta `401`:

- assinatura alterada;
- emissor ou audiência incorretos;
- finalidade incompatível ou capacidade ausente;
- expiração, `iat` futuro e lifetime superior a 300 segundos;
- `kid` desconhecido e algoritmo escolhido pela mensagem;
- estrutura JWS inválida e asserção acima de 16 KiB;
- repetição do mesmo `jti` enquanto presente no cache.

O Nexo apaga os cabeçalhos externos de identidade, reconstrói `sub` e
`request_id` somente após validação e executa a regra de domínio apenas para a
política `GET /api/v1/projects`.

## Bloco D — ponta a ponta e rotação

O teste decisivo comprovou:

```text
sessão humana autenticada
→ autorização nexo.projects.read no sisterd
→ asserção mínima assinada
→ validação pelo Nexo
→ GET /api/v1/projects
→ consulta PostgreSQL
→ resposta 200 com X-Request-ID verificado
```

O exercício de rotação comprovou:

1. chave A aceita;
2. A e B aceitas durante sobreposição;
3. B aceita após troca do emissor/consumidor;
4. A recusada como `unknown_key` após retirada.

## Reinício e risco residual

Uma asserção B já consumida foi reapresentada após reinício do Nexo e aceita
enquanto ainda válida. O resultado confirma a limitação documentada: o cache de
`jti` é local ao processo e não sobrevive a reinício.

Riscos residuais:

- replay dentro do TTL depois de reinício;
- distribuição manual das chaves;
- rotação comprovada em teste, ainda não ensaiada como procedimento operacional
  de implantação;
- ausência do gateway especializado;
- UBSan continua não executado no ambiente corrente por ausência da runtime.

## Decisão

**SEC-02V aprovado com restrição.** A identidade interna assinada está autorizada
somente para operação interna, read-only e shadow em `GET /api/v1/projects`.
O gate posterior [SEC-02M](./SEC-02M.md) torna essa política exata e separada do
proxy legado para incorporação na `v0.2.7`.

Não estão autorizadas:

- capacidades de escrita ou operações não idempotentes;
- exposição externa ou uso do `sisterd` como servidor HTTP público;
- promoção produtiva antes do SEC-03 e do procedimento governado de chaves.

No MAES-SisTer/1.0, `TH-IDENT-01` passa para `PARTIALLY_CONTROLLED`. O owner é
compartilhado entre manutenção de identidade do `sisterd`, manutenção do Nexo e
operação de plataforma.
