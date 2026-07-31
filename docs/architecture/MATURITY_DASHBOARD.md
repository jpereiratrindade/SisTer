# Painel de Maturidade

O Painel de Maturidade é uma funcionalidade administrativa de desenvolvimento.
Ele apresenta relatórios sanitizados produzidos pelos gates sem executar
comandos e sem recalcular aprovações.

## Fluxo

```text
scripts e testes -> verificador -> status JSON -> API admin -> painel
```

## Publicação

```bash
./scripts/maturity/run-and-publish.sh pre-alpha
```

Arquivos locais:

- `.run/maturity/latest.json`: última execução;
- `.run/maturity/history/index.json`: índice das execuções;
- `build/maturity/`: relatórios Markdown.

Esses diretórios não são versionados. A publicação preserva o código de saída
do gate, portanto uma execução reprovada ainda produz evidência e retorna erro.

## Acesso

- página: `/admin/maturity`;
- status: `GET /api/admin/maturity/latest`;
- histórico: `GET /api/admin/maturity/history`.

As rotas exigem sessão administrativa e respondem com `Cache-Control: no-store`.
Não existe endpoint para executar o gate.

## Diagnóstico

- `404`: nenhuma execução foi publicada;
- `503`: evidência ausente de schema conhecido, ilegível ou acima do limite;
- `401`: sessão ausente ou expirada;
- `403`: conta autenticada sem permissão administrativa.
