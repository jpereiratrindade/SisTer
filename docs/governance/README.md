# Governanca

O SisTer segue uma base inspirada no modelo do LabGestao:

- ADR para decisoes arquiteturais.
- DDD para fronteiras e linguagem ubiqua.
- DAI para decisoes, acoes e impedimentos.
- Politicas para fronteira de contexto, evidencia e aprovacao.
- Contratos de ferramenta para intervencoes assistidas por IA.
- Base conceitual viva conectada em `docs/conceptual`, descrita em `docs/CONCEPTUAL_BASE.md`.

Mudancas em contratos, ingestao, proveniencia e catalogo territorial devem registrar evidencia proporcional ao risco.

## Componentes governados

O estado atual do SisTer inclui componentes que devem ser tratados como superficie governada:

- `contracts/`: contratos JSON Schema e versoes de integracao.
- `examples/*_manifest_example.json`: contratos firmados ou exemplos de contrato por sistema integrante.
- `apps/sisterctl`: CLI de validacao, banco e operacao local.
- `apps/sisterd`: servidor/API inicial e entrega da interface.
- `web/`: interface de convergencia e diagnostico.
- `compose.yml`: orquestracao local do banco por ambiente.
- `docker/db/Dockerfile`: imagem PostgreSQL/pgvector.
- `storage/migrations/`: migrations SQL.
- `docs/governance/PUBLIC_PRIVATE_SCOPE.md`: politica de exposicao.

## Banco de dados e migrations

O banco operacional planejado neste incremento e PostgreSQL com pgvector.

Comandos operacionais:

```bash
./scripts/db/up.sh dev
export SISTER_DATABASE_URL='postgresql://sister:sister@localhost:55434/sister'
./scripts/db/check.sh dev
./scripts/db/migrate.sh dev
```

Regras de governanca:

- migrations devem ser versionadas em `storage/migrations/`;
- migrations precisam ser reaplicaveis ou declarar claramente quando nao forem;
- mudancas em tabelas com dados territoriais, evidencias, embeddings ou auditoria exigem DAI ou ADR;
- toda tabela operacional relevante deve possuir criterio de exposicao, preferencialmente `public_scope`;
- banco de desenvolvimento deve usar volume persistente, nao armazenamento efemero;
- credenciais reais nao devem ser commitadas.

## API e interface

O `sisterd` serve a interface e endpoints JSON iniciais:

- `/api/health`
- `/api/systems`
- `/api/contracts`
- `/api/evidence`
- `/api/diagnostics`
- `/api/integrations/sister-studio` (administrador, contrato externo)

Enquanto a API usar dados em memoria, a interface deve deixar claro quando indicadores forem demonstrativos. Quando a API passar a ler PostgreSQL, consultas de dashboard devem filtrar escopo de exposicao antes de retornar dados.

## Evidencias minimas por mudanca

Mudancas em banco, contratos, API ou governanca devem registrar pelo menos:

- comando de build/teste executado;
- validacao de contratos ou manifestos afetados;
- resultado de `db-check` quando a mudanca envolver banco;
- resultado de `db-migrate` quando a mudanca envolver migration;
- justificativa de escopo publico/restrito/privado quando houver exposicao de dados;
- DAI ou ADR quando a mudanca alterar fronteira arquitetural.

## LGPD e seguranca

O SisTer deve tratar governanca, LGPD e seguranca como criterios de desenho do produto, nao como texto decorativo.

Diretrizes iniciais:

- coletar e expor apenas dados necessarios para finalidade territorial declarada;
- preservar proveniencia e rastreabilidade de dados importados;
- registrar validacoes, rejeicoes e transformacoes relevantes;
- manter checksums de pacotes e evidencias quando aplicavel;
- separar transparencia operacional de exposicao indevida de dados sensiveis;
- exigir revisao proporcional ao risco para alteracoes em contratos, ingestao, catalogo, permissoes e auditoria.

A politica detalhada de exposicao esta em:

- [PUBLIC_PRIVATE_SCOPE.md](./PUBLIC_PRIVATE_SCOPE.md)
- [SISTER_STUDIO_DATA.md](./SISTER_STUDIO_DATA.md)
