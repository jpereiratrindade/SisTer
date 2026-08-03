# REL-PROD-MVP-01 — SisTer Core Produção MVP

Status: draft
Release de produto: v0.1.0
Tag Git recomendada: prod-mvp-v0.1.0
Branch alvo: main
Produto: SisTer Core
Maturidade funcional: Beta
Estado operacional autorizado: Produção MVP

## Atenção às Tags

A tag Git `v0.1.0` já existe e aponta para o protótipo inicial do repositório.
Ela é histórica e não deve ser movida, recriada ou sobrescrita.

Para o primeiro MVP operacional, use:

```text
prod-mvp-v0.1.0
```

Esse nome preserva a versão de produto `v0.1.0` sem conflitar com a linha
SemVer histórica do repositório, atualmente em `VERSION = 0.2.10`.

## Formulação Oficial

```text
O núcleo SisTer está tecnicamente pronto e, mediante autorização G6 para o
commit validado, pode ser promovido como primeiro MVP em produção controlada,
versão v0.1.0, mantendo maturidade funcional Beta.
```

## GitHub Release

Use este conteúdo como rascunho do GitHub Release somente após:

- `main` conter o commit validado;
- G1-G5 estarem `PASS`;
- G6 estar `AUTHORIZED` para o mesmo commit;
- `python3 scripts/prod01_readiness.py` retornar `Production authorized: true`.

### Título

```text
SisTer Core v0.1.0 — Produção MVP
```

### Tag

```text
prod-mvp-v0.1.0
```

### Target

```text
main
```

### Corpo

```md
# SisTer Core v0.1.0 — Produção MVP

Esta release marca o primeiro MVP operacional do SisTer Core em produção
controlada.

## Classificação

- Product maturity: Beta
- Core state: Produção MVP
- Operational state: Produção MVP
- Release de produto: v0.1.0
- Git tag: prod-mvp-v0.1.0

## Escopo

O núcleo SisTer entrega, em ambiente controlado:

- entrada pelo gateway HAProxy validado;
- autenticação e sessão;
- apresentação do ecossistema;
- consulta administrativa de maturidade;
- reconhecimento de contratos e subsistemas;
- separação entre integração declarada e capacidade operacional;
- isolamento entre testes dinâmicos de gateway e runtime operacional;
- preservação das rotas administrativas do núcleo.

## Ressalvas

- A maturidade funcional permanece Beta.
- Esta release promove o núcleo, não declara todos os subsistemas como plenamente
  operacionais.
- Sister-Clima, Sister-Studio e SisTer Nexo podem continuar em estados próprios
  de disponibilidade, desde que suas falhas não comprometam o núcleo.
- G6 deve estar autorizado para o mesmo commit publicado.
- A tag histórica v0.1.0 não foi reutilizada.

## Evidências

- PROD-01 readiness report: .run/production/prod01-readiness.json
- PROD-01 promotion report: .run/production/PROD-01-promotion-report.md
- Core state: .run/production/core-state.json
- Gateway/test isolation: docs/evidence/operations/PROD-01-G3-gateway-test-isolation.md
- PROD-01 closure playbook: docs/operations/PROD-01-CLOSURE.md

## Condição de Publicação

Publicar somente quando o comando abaixo indicar autorização:

```bash
python3 scripts/prod01_readiness.py
```

Resultado exigido:

```text
Technical status ........ READY
Decision ................ AUTHORIZED
Production authorized ... true
MVP version ............. v0.1.0
Product maturity ........ Beta
Core state .............. Produção MVP
Operational state ....... Produção MVP
Recommended tag ......... prod-mvp-v0.1.0
```
```

## Comandos de Publicação

Executar somente após G6:

```bash
git status --short
git rev-parse HEAD
python3 scripts/prod01_readiness.py
git push origin main
git tag -a prod-mvp-v0.1.0 -m "SisTer Core v0.1.0 — Produção MVP"
git push origin prod-mvp-v0.1.0
```

Não execute estes comandos enquanto `Production authorized` for `false`.
