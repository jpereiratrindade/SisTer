# Norma de Engenharia: Padrão Operacional de Git para Subsistemas SisTer

**Documento:** `GIT_WORKFLOW_STANDARD.md`  
**Versão:** 1.0.0  
**Data:** 2026-08-25  
**Status:** `NORMATIVO / PADRÃO DE ENGENHARIA`  
**Escopo:** Todos os repositórios e participantes do ecossistema SisTer (`SisTer`, `sister-infra`, `sister-praxis`, `sister-nexo`, `sister-urt`, `sister-atmos`, etc.)

---

## 1. Princípios Fundamentais

O controle de versão no ecossistema SisTer baseia-se em quatro pilares fundamentais:
1. **Rastreabilidade e Auditabilidade**: Cada commit deve representar uma unidade semântica clara e verificável no tempo.
2. **Não-Destrutividade**: Operações destrutivas automáticas são proibidas; o trabalho existente nunca deve ser descartado às cegas.
3. **Isolamento de Mudanças**: Frentes de trabalho distintas não devem ser misturadas no mesmo ramo ou commit.
4. **Garantia de Não-Regressão**: Nenhum código é integrado sem compilação limpa e 100% de sucesso nos testes automatizados.

---

## 2. Modus Operandi Pré-Edição (Inspeção de Baseline)

Antes de iniciar qualquer modificação no código ou nos contratos:

```bash
# 1. Identificar branch atual e remotos
git branch --show-current
git remote -v

# 2. Registrar o HEAD de partida
git log -1 --oneline --decorate

# 3. Atualizar referências remotas (sem aplicar merge automático)
git fetch --all --prune

# 4. Inspecionar o estado da working tree
git status --short
```

### 2.1. Tratamento de Working Tree Suja
Se houver alterações não comitadas:
* **Proibição Estrita**: **Nunca** executar comandos destrutivos automáticos:
  ```bash
  # NUNCA EXECUTAR AUTOMATICAMENTE:
  git reset --hard
  git clean -fd
  git checkout -- .
  ```
* **Procedimento Correto**: Inspecionar com `git diff` e `git diff --staged` e obter alinhamento prévio antes de prosseguir.

---

## 3. Estratégia de Branches

1. **Ponto de Partida Limpo**: O branch de desenvolvimento deve obrigatoriamente nascer de um commit conhecido, limpo e testado do ramo principal (`main` ou `master`).
2. **Separação de Escopo**: Se outra frente estiver em andamento no repositório, criar um branch dedicado e nunca misturar implementações conceituais distintas.
3. **Convenção de Nomenclatura**:
   - `feature/<nome-curto>`: Novas capacidades ou funcionalidades.
   - `refactor/<nome-curto>`: Refatorações estruturais sem alteração de comportamento externo.
   - `fix/<nome-curto>`: Correção de defeitos ou falhas de conformidade.
   - `docs/<nome-curto>`: Atualizações de documentação e contratos.

---

## 4. Práticas de Desenvolvimento e Staging

1. **Inspeção Contínua**:
   - Executar frequentemente `git status --short`, `git diff` e `git diff --stat`.
   - Rodar `git diff --check` para detectar problemas de whitespace, quebras de linha e caracteres espúrios antes de adicionar ao stage.
2. **Staging Explícito (Proibido `git add .` às cegas)**:
   - Fazer stage adicionando arquivos explicitamente:
     ```bash
     git add src/domain.cpp include/sister/domain.hpp
     ```
   - Usar `git add -p` quando houver alterações distintas no mesmo arquivo, assegurando que mudanças interdependentes não sejam fragmentadas de forma incoerente.
   - Verificar rigorosamente o stage antes de commitar:
     ```bash
     git diff --cached
     git diff --cached --stat
     ```

---

## 5. Formação e Criação de Commits

### 5.1. Unicidade Semântica
Cada commit deve responder com precisão à pergunta:
> **"Qual mudança arquitetural ou funcional completa este commit representa?"**

* Não combinar múltiplos objetivos não relacionados (ex: contrato de manifesto + alteração de CSS + correção de banco + ajuste de infraestrutura) em um único commit.

### 5.2. Padrão de Mensagens (Conventional Commits)
Evitar mensagens genéricas como *"updates"*, *"fix stuff"*, *"changes"* ou *"final"*.

Prefixos padronizados:
* `feat(<escopo>)`: Nova funcionalidade ou contrato.
* `fix(<escopo>)`: Correção de bug ou inconsistência.
* `refactor(<escopo>)`: Reestruturação interna sem alteração comportamental.
* `test(<escopo>)`: Inclusão ou ajuste de testes automatizados.
* `docs(<escopo>)`: Atualizações de documentação técnica ou especificações.
* `chore(<escopo>)`: Tarefas de manutenção, `.gitignore`, dependências de build.

### 5.3. Gate Obrigatório Pré-Commit
Antes de criar o commit, cumprir o seguinte checklist:
1. `git diff --check` retorna código zero (sem erros de whitespace).
2. `git diff --cached` inspecionado linha por linha.
3. Compilação do projeto com flags estritas (`-Werror`).
4. Execução de 100% da suíte de testes com aprovação (`ctest` / scripts de teste).

```bash
# Somente após os gates acima passarem:
git commit -m "feat(web): expose subsystem publication manifest"
```

### 5.4. Verificação Pós-Commit
Após commitar, validar imediatamente o resultado:
```bash
git status -sb
git log -1 --oneline --decorate
git show --stat --oneline HEAD
git show --check HEAD
```

---

## 6. Merge e Integração

1. **Merge Não-Automático**: Não integrar em `main` antes da validação de todos os critérios de aceitação.
2. **Inspeção de Diferença Total**:
   ```bash
   git diff main...HEAD --stat
   git diff --check main...HEAD
   ```
3. **Preferência por Fast-Forward**:
   ```bash
   git switch main
   git pull --ff-only origin main
   git merge --ff-only <branch>
   ```
4. **Sem Improviso em Caso de Conflito**: Se o merge fast-forward não for possível, relatar a divergência para avaliação de rebase versus merge commit explicativo.

---

## 7. Sincronização com Remotos (Push)

1. **Verificação de Consistência**:
   ```bash
   git status -sb
   git log -1 --oneline --decorate
   ```
2. **Múltiplos Remotos (Espelhos GitHub / GitLab)**:
   - Fazer push primeiro para o remoto principal (`origin`):
     ```bash
     git push origin <branch>
     ```
   - Se houver espelho oficial (ex: `gitlab`), sincronizar em seguida com o mesmo commit:
     ```bash
     git push gitlab <branch>
     ```
   - Confirmar que ambos os remotos apontam para o mesmo hash SHA.
3. **Proibição de Força**:
   - **Estritamente proibido** utilizar `git push --force` ou `git push --force-with-lease` sem justificativa formal e autorização humana prévia.

---

## 8. Arquivos Estritamente Proibidos no Repositório (.gitignore)

Nunca incluir no controle de versão:
* Artefatos de compilação e diretórios temporários (`build/`, `bin/`, `out/`, `target/`, `tmp/`).
* Logs e rastros de execução (`logs/`, `*.log`).
* Segredos, credenciais e arquivos de ambiente (`.env`, `secrets/`, chaves privadas, certificados TLS, tokens de API).
* Dumps de bancos de dados ou registros transacionais de usuários.
