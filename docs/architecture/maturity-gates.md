# Verificador dos gates de maturidade do SisTer

Este pacote transforma o roteiro **Pré-Alfa → Alfa → Beta → Gama → Produção**
em verificações executáveis e em uma atestação vinculada ao commit Git.

## O que ele atesta

O script comprova que:

- os artefatos esperados existem;
- os testes oficiais do repositório foram executados com sucesso;
- antipadrões bloqueantes não permanecem no código;
- aprovações humanas exigidas foram registradas;
- o commit e a configuração usados no gate estão identificados.

Ele **não** afirma sozinho que o sistema é correto ou seguro. A qualidade da
atestação depende da qualidade dos testes e das evidências versionadas.

## Instalação

```bash
mkdir -p scripts
cp verify-sister-maturity.sh scripts/
chmod +x scripts/verify-sister-maturity.sh

mkdir -p .sister
cp maturity.conf.example .sister/maturity.conf

./scripts/verify-sister-maturity.sh --init --repo .
```

O comando `--init` cria diretórios de evidência e a configuração inicial, mas
não cria testes que passem automaticamente.

## Comandos principais

```bash
# Baseline atual
./scripts/verify-sister-maturity.sh --stage pre-alpha

# Fundações
./scripts/verify-sister-maturity.sh --stage alpha \
  --report build/alpha-report.md

# Integração, incluindo endpoints em execução
./scripts/verify-sister-maturity.sh --stage beta --runtime \
  --report build/beta-report.md

# Pré-produção
./scripts/verify-sister-maturity.sh --stage gamma --strict \
  --report build/gamma-report.md

# Atestação vinculada ao commit
./scripts/verify-sister-maturity.sh --stage gamma --mode certify \
  --report build/gamma-report.md

# Atestação assinada
./scripts/verify-sister-maturity.sh --stage production --mode certify \
  --gpg-key ABCDEF1234567890
```

## Scripts oficiais esperados

O gate não embute a implementação dos testes. Ele executa os scripts oficiais
do repositório, que devem existir e falhar quando o requisito não for atendido:

```text
scripts/verify-identical.sh
scripts/ci/test-smoke.sh
scripts/ci/test-unit.sh
scripts/ci/test-contract.sh
scripts/ci/test-integration.sh
scripts/ci/test-security.sh
scripts/ci/test-load.sh
scripts/ci/test-recovery.sh
scripts/ci/test-backup-restore.sh
scripts/ci/test-key-rotation.sh
scripts/ci/test-rollback.sh
scripts/ci/validate-gateway.sh
```

Cada script deve:

1. usar `set -Eeuo pipefail`;
2. produzir saída legível;
3. retornar `0` somente quando a evidência estiver aprovada;
4. retornar valor diferente de `0` em falha;
5. não alterar silenciosamente dados reais.

## Aprovações humanas

Os arquivos de aprovação ficam em:

```text
docs/evidence/alpha/
docs/evidence/beta/
docs/evidence/gamma/
docs/evidence/production/
```

Exemplo:

```yaml
stage: gamma
area: security
status: approved
commit: 0123456789abcdef...
approved_by: responsável de segurança
approved_at: 2026-08-15T14:00:00-03:00
evidence:
  - build/security-report.md
  - docs/threat-model/risk-register.md
notes: sem riscos críticos abertos
```

O modo `certify` exige árvore Git limpa. A atestação registra:

- commit;
- branch;
- hash do verificador;
- hash da configuração;
- ambiente de execução;
- todos os checks e resultados.

## Relação entre gates

Ao verificar `beta`, o script executa também Pré-Alfa e Alfa.
Ao verificar `gamma`, executa Pré-Alfa, Alfa e Beta.
Produção somente passa depois de todos os gates anteriores.

## Integração com CI

Exemplo:

```yaml
maturity-gamma:
  script:
    - ./scripts/verify-sister-maturity.sh
        --stage gamma
        --strict
        --report build/gamma-report.md
  artifacts:
    when: always
    paths:
      - build/gamma-report.md
```

O gate de produção deve ser protegido e executado sobre commit marcado com uma
tag SemVer estável. Ative `REQUIRE_SIGNED_TAG=1` quando a equipe já tiver
política de assinatura de tags estabelecida.
