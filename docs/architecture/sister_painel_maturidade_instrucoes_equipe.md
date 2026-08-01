# SisTer — Instruções para Implementação do Painel de Maturidade

**Projeto:** SisTer — Sistema Inteligente e Resiliência de SSE
**Componente:** Painel de Maturidade do Desenvolvimento
**Status:** instrução de execução para a equipe
**Escopo inicial:** Pré-Alfa, Alfa, Beta, Gama e Produção
**Princípio:** a interface exibe evidências; o verificador continua sendo a autoridade sobre os gates.

---

## 1. Decisão arquitetural

Criar uma interface web para mostrar o estado de maturidade do SisTer faz sentido e fortalece a estratégia de engenharia, desde que sejam preservadas quatro regras:

1. **a interface não calcula nem altera o resultado dos gates;**
2. **o script `verify-sister-maturity.sh` permanece como autoridade de verificação;**
3. **o painel consome um relatório JSON versionado e sanitizado;**
4. **a primeira versão é somente leitura e não executa comandos a partir do navegador.**

O Painel de Maturidade não deve ser tratado como subsistema científico ou operacional. Ele pertence ao **plano de controle, observabilidade e governança do desenvolvimento do SisTer**.

A responsabilidade fica assim:

```text
scripts e testes
      │
      ▼
verify-sister-maturity.sh
      │ produz evidência
      ▼
maturity-status.json
      │ somente leitura
      ▼
Painel de Maturidade
```

> O verificador atesta; o painel comunica.

---

## 2. Objetivo da primeira versão

A versão inicial deve permitir que a equipe veja, em uma única página:

- estágio atual do SisTer;
- gate-alvo da última execução;
- resultado geral;
- quantidade de verificações aprovadas, reprovadas, advertidas e ignoradas;
- commit e branch avaliados;
- indicação de árvore Git limpa ou alterada;
- data da última verificação;
- versão do verificador;
- checks agrupados por Pré-Alfa, Alfa, Beta, Gama e Produção;
- bloqueios que impedem a promoção;
- evidências associadas;
- próxima etapa recomendada;
- histórico recente de execuções.

A interface não deve mostrar:

- senhas;
- cookies;
- tokens;
- chaves;
- URLs com credenciais;
- caminhos absolutos do computador;
- saída bruta sem sanitização;
- conteúdo arbitrário de arquivos do repositório.

---

## 3. Estratégia de implementação

A implementação será dividida em três entregas.

### Entrega A — contrato e publicação do estado

Objetivo: produzir uma fonte de dados estável e legível por máquina.

### Entrega B — interface web somente leitura

Objetivo: mostrar o resultado sem alterar o verificador e sem executar comandos.

### Entrega C — histórico e integração administrativa

Objetivo: registrar evolução, comparar execuções e integrar o painel à área administrativa do SisTer.

A equipe não deve começar pela interface visual. O primeiro artefato é o contrato JSON. Sem contrato, a tela vira um leitor elegante de improvisos.

---

## 4. Estrutura recomendada no repositório

Criar:

```text
SisTer/
├── contracts/
│   └── maturity/
│       └── 1.0.0/
│           ├── maturity-status.schema.json
│           ├── maturity-history.schema.json
│           ├── example.json
│           └── README.md
├── scripts/
│   └── maturity/
│       ├── run-and-publish.sh
│       ├── sanitize-attestation.py
│       └── validate-status.py
├── web/
│   └── maturity/
│       ├── index.html
│       ├── app.js
│       └── styles.css
├── tests/
│   └── maturity/
│       ├── test_status_schema.py
│       ├── test_sanitization.py
│       └── test_dashboard_smoke.py
├── docs/
│   ├── adr/
│   │   └── ADR-0010-maturity-dashboard.md
│   └── architecture/
│       └── MATURITY_DASHBOARD.md
└── .run/
    └── maturity/
        ├── latest.json
        └── history/
```

Regras:

- `.run/maturity/` não deve ser versionado;
- exemplos e schemas devem ser versionados;
- relatórios reais devem ser produzidos localmente ou pela CI;
- o painel não deve ler diretamente `.sister/maturity.conf`;
- o painel não deve varrer o repositório;
- o painel não deve executar shell.

Adicionar ao `.gitignore`:

```gitignore
.run/maturity/
build/maturity/
```

---

## 5. Contrato `sister.maturity-status/1.0.0`

Criar o schema:

```text
contracts/maturity/1.0.0/maturity-status.schema.json
```

Modelo inicial:

```json
{
  "schema": "sister.maturity-status/1.0.0",
  "project": "SisTer",
  "target_stage": "pre-alpha",
  "result": "PASS",
  "generated_at": "2026-07-31T13:30:00Z",
  "verifier_version": "1.0.0",
  "source": {
    "commit": "0123456789abcdef",
    "short_commit": "0123456789ab",
    "branch": "main",
    "dirty": true
  },
  "summary": {
    "total": 9,
    "passed": 8,
    "failed": 0,
    "warned": 1,
    "skipped": 0,
    "mandatory_failures": 0
  },
  "stages": [
    {
      "id": "pre-alpha",
      "label": "Pré-Alfa",
      "state": "approved",
      "checks": [
        {
          "id": "baseline-integrity",
          "status": "PASS",
          "mandatory": true,
          "description": "Snapshot permanece íntegro",
          "detail": "Verificação concluída",
          "evidence": [
            "labs/sisterd_lab/manifests/target.sha256"
          ]
        }
      ]
    }
  ],
  "blockers": [],
  "next_actions": [
    "Consolidar alterações em commits revisados",
    "Executar o gate em modo certify"
  ],
  "attestation": {
    "available": false,
    "signed": false,
    "relative_path": null
  }
}
```

### Valores permitidos

Para `result`:

```text
PASS
FAIL
```

Para o estado de cada estágio:

```text
approved
in_progress
blocked
not_started
```

Para checks:

```text
PASS
FAIL
WARN
SKIP
```

### Regras de sanitização

O JSON publicado para a interface deve:

- usar caminhos relativos;
- remover o caminho absoluto do repositório;
- limitar `detail` a tamanho conhecido;
- remover sequências de controle;
- não copiar saída integral de testes;
- nunca incluir variáveis de ambiente;
- nunca incluir comandos com credenciais;
- nunca incluir corpos de autenticação;
- nunca incluir tokens ou cookies.

---

## 6. Alteração necessária no verificador

O script atual produz relatório Markdown e, no modo `certify`, atestação JSON. A interface não deve analisar a saída colorida do terminal nem extrair dados do Markdown.

Adicionar ao verificador uma opção explícita:

```text
--status-json <arquivo>
```

Exemplo:

```bash
./scripts/verify-sister-maturity.sh \
  --stage pre-alpha \
  --report build/maturity/pre-alpha-report.md \
  --status-json .run/maturity/latest.json
```

A opção deve funcionar em `check` e `certify`.

### Requisitos

- escrita atômica: gerar arquivo temporário e depois usar `mv`;
- schema fixo e versionado;
- saída sanitizada;
- código de saída do gate preservado;
- nenhuma aprovação criada pela interface;
- nenhum resultado recalculado pelo JavaScript.

Caso a equipe prefira não alterar imediatamente o script principal, pode criar:

```text
scripts/maturity/sanitize-attestation.py
```

Esse utilitário deve receber a atestação ou resultado estruturado e gerar o JSON público. Não deve analisar texto livre do terminal como solução permanente.

---

## 7. Publicador do estado

Criar:

```text
scripts/maturity/run-and-publish.sh
```

Responsabilidades:

1. receber somente um estágio permitido;
2. criar diretórios necessários;
3. executar o verificador;
4. gerar relatório Markdown;
5. gerar JSON sanitizado;
6. validar o JSON contra o schema;
7. publicar `latest.json` atomicamente;
8. arquivar uma cópia no histórico;
9. preservar o código de saída do gate.

O arquivo é uma implementação interna. O uso operacional suportado ocorre pela
CLI SGE:

```bash
./scripts/sge maturity publish pre-alpha
```

Saídas:

```text
build/maturity/pre-alpha-report.md
.run/maturity/latest.json
.run/maturity/history/20260731T133000Z-pre-alpha-0123456789ab.json
```

O script deve aceitar apenas:

```text
pre-alpha
alpha
beta
gamma
production
```

Nunca deve aceitar caminho de repositório, comando ou nome de script vindo do navegador.

---

## 8. Interface web

Criar:

```text
web/maturity/
├── index.html
├── app.js
└── styles.css
```

### Rota recomendada

```text
/admin/maturity
```

O painel deve ser visível somente para identidades que possuam:

```text
maturity.evidence.read
```

O mapeamento inicial concede essa capacidade ao papel `admin`, mas os handlers
não devem repetir uma verificação direta de papel.

### Componentes da página

#### Cabeçalho

Mostrar:

- “Painel de Maturidade do SisTer”;
- estágio atual;
- resultado geral;
- última atualização;
- commit avaliado.

#### Linha de maturidade

```text
Pré-Alfa → Alfa → Beta → Gama → Produção
```

Cada estágio deve mostrar texto e ícone, não apenas cor.

#### Resumo

Cartões:

- aprovados;
- falhas;
- advertências;
- ignorados;
- falhas obrigatórias.

#### Bloqueadores

Lista prioritária dos checks `FAIL` obrigatórios.

Se não houver bloqueios:

```text
Nenhum bloqueio obrigatório na última verificação.
```

#### Checks por estágio

Tabela com:

- estado;
- identificador;
- descrição;
- obrigatoriedade;
- evidência;
- detalhe sanitizado.

#### Proveniência

Mostrar:

- commit;
- branch;
- árvore limpa/alterada;
- versão do verificador;
- schema;
- assinatura disponível;
- horário da execução.

#### Próximas ações

Mostrar as ações registradas no JSON, sem inferência livre no navegador.

#### Histórico

Na primeira versão, mostrar no máximo as dez execuções mais recentes.

---

## 9. Aparência e acessibilidade

A interface deve:

- funcionar em modo claro e escuro;
- não depender exclusivamente de verde, amarelo e vermelho;
- usar rótulos `Aprovado`, `Falhou`, `Advertência` e `Ignorado`;
- permitir navegação por teclado;
- usar HTML semântico;
- possuir contraste adequado;
- ter tabela responsiva;
- oferecer texto alternativo para ícones;
- manter leitura útil sem animações;
- não usar gráficos decorativos que escondam os checks.

Sugestão visual:

```text
┌──────────────────────────────────────────────────────────┐
│ Painel de Maturidade do SisTer                           │
│ Gate atual: Pré-Alfa — APROVADO COM ADVERTÊNCIA          │
│ Commit: 0123456789ab · main · árvore alterada             │
├──────────────────────────────────────────────────────────┤
│ Pré-Alfa ✓   Alfa ○   Beta ○   Gama ○   Produção ○       │
├──────────────────────────────────────────────────────────┤
│ PASS 8   FAIL 0   WARN 1   SKIP 0   BLOQUEIOS 0          │
├──────────────────────────────────────────────────────────┤
│ Bloqueadores                                             │
│ Nenhum bloqueio obrigatório                              │
├──────────────────────────────────────────────────────────┤
│ Verificações                                             │
│ ✓ baseline-integrity                                     │
│ ✓ smoke-flow                                             │
│ ! git-clean                                              │
├──────────────────────────────────────────────────────────┤
│ Próxima ação: consolidar commit e executar certify       │
└──────────────────────────────────────────────────────────┘
```

---

## 10. Como servir o JSON com segurança

### Primeira versão recomendada

Não colocar o JSON real diretamente no diretório público sem controle de acesso.

Criar uma rota administrativa somente leitura:

```http
GET /api/admin/maturity/latest
```

Ela deve:

- exigir autenticação;
- exigir `admin` na fase atual;
- depois exigir `maturity.evidence.read`;
- ler somente o arquivo fixo `.run/maturity/latest.json`;
- limitar o tamanho do arquivo;
- validar o schema ou ao menos o cabeçalho;
- responder `404` quando nunca houve execução;
- responder `503` quando o arquivo estiver inválido;
- aplicar `Cache-Control: no-store`;
- nunca aceitar caminho informado pelo usuário.

Na arquitetura futura, essa rota poderá migrar para um módulo genérico de evidências. Nesta etapa, ela é uma ponte controlada.

### Proibido na primeira versão

Não implementar:

```http
POST /api/admin/maturity/run
```

A interface não deve disparar o shell na primeira versão.

O botão “Atualizar” deve apenas refazer o `GET`.

A execução continuará sendo realizada:

- pela equipe no terminal;
- pela CI;
- por unidade `systemd` ou timer, quando aprovado.

---

## 11. Histórico

Criar um índice sanitizado:

```text
.run/maturity/history/index.json
```

Exemplo:

```json
{
  "schema": "sister.maturity-history/1.0.0",
  "items": [
    {
      "generated_at": "2026-07-31T13:30:00Z",
      "target_stage": "pre-alpha",
      "result": "PASS",
      "short_commit": "0123456789ab",
      "passed": 8,
      "failed": 0,
      "warned": 1,
      "relative_path": "history/20260731T133000Z-pre-alpha-0123456789ab.json"
    }
  ]
}
```

Regras:

- no máximo 100 registros locais por padrão;
- ordenação por data decrescente;
- sem caminhos absolutos;
- sem logs brutos;
- retenção configurável;
- histórico assinado somente quando houver atestação formal.

---

## 12. Testes obrigatórios

### Testes do contrato

- JSON válido;
- schema correto;
- estágio permitido;
- contagens não negativas;
- checks com estados permitidos;
- ausência de campos desconhecidos críticos;
- caminhos relativos;
- limite de tamanho.

### Testes de sanitização

- remove caminho absoluto;
- remove token;
- remove cookie;
- remove senha;
- remove caracteres de controle;
- limita detalhe;
- rejeita arquivo inválido.

### Testes da API

- usuário não autenticado recebe `401`;
- usuário sem permissão recebe `403`;
- administrador recebe `200`;
- arquivo ausente recebe `404`;
- arquivo inválido recebe `503`;
- resposta possui `no-store`;
- caminho não pode ser alterado por query string.

### Testes da interface

- carrega JSON válido;
- exibe resultado;
- exibe advertência;
- exibe bloqueadores;
- exibe estado vazio;
- exibe erro de API;
- não interpreta HTML vindo do JSON;
- funciona sem depender apenas de cores.

### Smoke test

Adicionar ao smoke:

```text
GET /admin/maturity
GET /api/admin/maturity/latest
```

O smoke não deve executar um gate; apenas confirmar que o painel consegue ler uma evidência preparada de teste.

---

## 13. Ordem de execução para a equipe

### Passo 1 — ADR

Criar:

```text
docs/adr/ADR-0010-maturity-dashboard.md
```

Decisão:

> O Painel de Maturidade será uma interface somente leitura sobre relatórios estruturados produzidos pelo verificador. O painel não executa gates nem decide aprovação.

### Passo 2 — contrato

Criar e validar:

```text
contracts/maturity/1.0.0/maturity-status.schema.json
```

### Passo 3 — saída JSON

Adicionar `--status-json` ao verificador ou criar publicador estruturado equivalente.

### Passo 4 — sanitização

Criar testes que provem a ausência de caminhos absolutos e segredos.

### Passo 5 — publicador

Implementar o publicador interno `run-and-publish.sh` e expô-lo somente por
`./scripts/sge maturity publish`.

### Passo 6 — API somente leitura

Implementar:

```http
GET /api/admin/maturity/latest
```

### Passo 7 — página web

Implementar a tela sem botão de execução.

### Passo 8 — testes

Executar contrato, API, frontend e smoke.

### Passo 9 — documentação

Registrar instalação, uso, riscos e troubleshooting.

### Passo 10 — integração ao gate

Adicionar ao gate Alfa checks para:

- contrato de maturidade;
- JSON validado;
- API protegida;
- teste de sanitização;
- painel web;
- smoke do painel.

---

## 14. Pacotes de trabalho

### MD-01 — Contrato de status

**Responsável:** arquitetura/contratos
**Entrega:** schemas e exemplos
**Aceite:** exemplos válidos e inválidos testados.

### MD-02 — Exportação estruturada

**Responsável:** engenharia de ferramentas
**Entrega:** `--status-json` e escrita atômica
**Aceite:** o JSON representa exatamente o resultado do gate.

### MD-03 — Sanitização

**Responsável:** segurança
**Entrega:** sanitizador e testes
**Aceite:** nenhum segredo ou caminho absoluto aparece.

### MD-04 — API administrativa

**Responsável:** `sisterd`
**Entrega:** endpoint somente leitura
**Aceite:** `401`, `403`, `404`, `503` e `200` testados.

### MD-05 — Interface

**Responsável:** frontend
**Entrega:** página responsiva e acessível
**Aceite:** estados PASS, FAIL, WARN, SKIP e ausência de dados exibidos corretamente.

### MD-06 — Histórico

**Responsável:** ferramentas/observabilidade
**Entrega:** índice e retenção
**Aceite:** últimas execuções consultáveis sem exposição de dados sensíveis.

### MD-07 — CI

**Responsável:** qualidade
**Entrega:** geração e publicação de artefatos
**Aceite:** cada pipeline produz relatório e JSON, mesmo em falha.

---

## 15. Definition of Done da primeira versão

A primeira versão estará concluída quando:

- [ ] existir contrato JSON versionado;
- [ ] o verificador produzir saída estruturada;
- [ ] a publicação for atômica;
- [ ] o JSON público estiver sanitizado;
- [ ] a API for somente leitura;
- [ ] a API exigir autorização;
- [ ] a interface mostrar todos os gates;
- [ ] os bloqueadores estiverem destacados;
- [ ] commit, branch e estado da árvore forem exibidos;
- [ ] a interface não executar comandos;
- [ ] testes de contrato passarem;
- [ ] testes de sanitização passarem;
- [ ] testes de autorização passarem;
- [ ] smoke da interface passar;
- [ ] ADR e documentação estiverem versionados;
- [ ] o próprio gate verificar a existência e a conformidade do painel.

---

## 16. Evolução posterior

Somente após a primeira versão estar estável, avaliar:

### Versão 0.2

- histórico comparativo;
- tendências por check;
- integração com CI;
- link para relatório Markdown;
- assinatura e validação de atestações;
- capacidade `maturity.evidence.read`.

### Versão 0.3

- execução agendada por `systemd timer`;
- notificações de regressão;
- comparação entre commits;
- duração dos testes;
- painel de riscos e ADRs pendentes.

### Versão 1.0

- persistência do histórico no PostgreSQL;
- trilha de promoção;
- aprovações eletrônicas;
- assinatura obrigatória;
- integração com releases;
- capacidade controlada para solicitar execução.

Mesmo na versão 1.0, o navegador não deverá executar comando arbitrário. Uma solicitação de verificação deverá criar um job com estágio enumerado, ambiente fixo, limites, auditoria e processo isolado.

---

## 17. Resultado esperado

Ao final da primeira versão, a equipe poderá abrir o Painel de Maturidade e responder imediatamente:

- em que estágio o SisTer está;
- qual commit foi verificado;
- quais gates já passaram;
- o que impede a promoção;
- quais evidências sustentam o resultado;
- quando a última verificação ocorreu;
- qual é a próxima ação de engenharia.

A interface dará corpo ao sistema de verificação sem transformar aparência em autoridade.

> **O painel torna o progresso visível; os gates tornam o progresso confiável.**
