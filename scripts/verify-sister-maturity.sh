#!/usr/bin/env bash
# SisTer maturity gate verifier
# Verifica e, opcionalmente, atesta os gates Pré-Alfa, Alfa, Beta, Gama e Produção.
# A atestação comprova que os checks configurados passaram em um commit específico;
# ela não substitui revisão técnica, de segurança ou aceite humano.

set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_VERSION="1.0.0"
TARGET_STAGE=""
MODE="check"
REPO=""
CONFIG_FILE=""
REPORT_FILE=""
ATTESTATION_FILE=""
STATUS_JSON_FILE=""
GPG_KEY=""
RUNTIME_CHECKS=0
STRICT=0
NO_COLOR=0
VERBOSE=0
ENGINE="compare"

declare -A STAGE_RANK=(
  [pre-alpha]=0
  [alpha]=1
  [beta]=2
  [gamma]=3
  [production]=4
)

# Caminhos de scripts de evidência. Podem ser sobrescritos por .sister/maturity.conf.
VERIFY_IDENTICAL="scripts/verify-identical.sh"
SMOKE_TEST="scripts/ci/test-smoke.sh"
UNIT_TEST="scripts/ci/test-unit.sh"
CONTRACT_TEST="scripts/ci/test-contract.sh"
INTEGRATION_TEST="scripts/ci/test-integration.sh"
SECURITY_TEST="scripts/ci/test-security.sh"
LOAD_TEST="scripts/ci/test-load.sh"
RECOVERY_TEST="scripts/ci/test-recovery.sh"
BACKUP_RESTORE_TEST="scripts/ci/test-backup-restore.sh"
KEY_ROTATION_TEST="scripts/ci/test-key-rotation.sh"
ROLLBACK_TEST="scripts/ci/test-rollback.sh"
GATEWAY_VALIDATE="scripts/ci/validate-gateway.sh"

BASE_URL="http://127.0.0.1:8000"
CLIMA_HEALTH_URL="http://127.0.0.1:8501/_sister/health"
NEXO_HEALTH_URL="http://127.0.0.1:8015/_sister/health"
MIN_RUNBOOKS=10
REQUIRE_SIGNED_TAG=0

TMP_RESULTS=""
TOTAL=0
PASSED=0
FAILED=0
WARNED=0
SKIPPED=0
MANDATORY_FAILURES=0
INITIAL_GIT_DIRTY="false"

usage() {
  cat <<'EOF'
Uso:
  verify-sister-maturity.sh --stage <pre-alpha|alpha|beta|gamma|production> [opções]

Modos:
  --mode check       Executa os gates e produz relatório. Padrão.
  --mode certify     Exige repositório limpo e gera atestação JSON.
  --init             Cria apenas a estrutura inicial de configuração/evidências.
                     Não cria testes que passem automaticamente.

Opções:
  --repo <caminho>          Raiz do repositório. Padrão: raiz Git atual.
  --config <arquivo>        Configuração. Padrão: .sister/maturity.conf.
  --report <arquivo.md>     Salva relatório Markdown.
  --attestation <arquivo>   Caminho da atestação JSON em modo certify.
  --status-json <arquivo>   Publica status JSON sanitizado em qualquer modo.
  --engine <modo>           Define o motor: legacy, declarative, compare (padrão: legacy).
  --runtime                 Verifica endpoints em execução.
  --strict                  Converte avisos em falhas.
  --gpg-key <id>            Assina a atestação com GPG.
  --verbose                 Exibe saída dos scripts de teste.
  --no-color                Desativa cores.
  -h, --help                Mostra esta ajuda.

Exemplos:
  ./scripts/verify-sister-maturity.sh --stage alpha
  ./scripts/verify-sister-maturity.sh --stage beta --runtime
  ./scripts/verify-sister-maturity.sh --stage gamma --mode certify \
    --report build/gamma-report.md --gpg-key ABCDEF1234567890

Semântica:
  pre-alpha  congela e comprova o baseline;
  alpha      prova arquitetura, contrato, sessões e identidade;
  beta       prova integração por gateway e adaptadores;
  gamma      prova operação, segurança e recuperação;
  production promove somente após todos os gates anteriores.
EOF
}

die() {
  printf 'ERRO: %s\n' "$*" >&2
  exit 2
}

color_init() {
  if [[ -t 1 && "$NO_COLOR" -eq 0 ]]; then
    C_RED=$'\033[31m'
    C_GREEN=$'\033[32m'
    C_YELLOW=$'\033[33m'
    C_BLUE=$'\033[34m'
    C_BOLD=$'\033[1m'
    C_RESET=$'\033[0m'
  else
    C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_BOLD=""; C_RESET=""
  fi
}

sanitize_field() {
  local value="${1//$'\t'/ }"
  value="${value//$'\n'/ }"
  value="${value//$'\r'/ }"
  printf '%s' "$value"
}

check_id_slug() {
  local value="$1"
  value="$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')"
  value="${value//[^a-z0-9]/-}"
  value="$(printf '%s' "$value" | sed -E 's/-+/-/g; s/^-//; s/-$//')"
  printf '%s' "${value:-check}"
}

sha256_file() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file" | awk '{print $1}'
  else
    printf 'unavailable'
  fi
}

stage_enabled() {
  local stage="$1"
  (( STAGE_RANK[$stage] <= STAGE_RANK[$TARGET_STAGE] ))
}

record_result() {
  local status="$1" stage="$2" id="$3" mandatory="$4" description="$5" detail="${6:-}"
  TOTAL=$((TOTAL + 1))
  case "$status" in
    PASS) PASSED=$((PASSED + 1));;
    FAIL)
      FAILED=$((FAILED + 1))
      [[ "$mandatory" == "yes" ]] && MANDATORY_FAILURES=$((MANDATORY_FAILURES + 1))
      ;;
    WARN)
      WARNED=$((WARNED + 1))
      if [[ "$STRICT" -eq 1 ]]; then
        FAILED=$((FAILED + 1))
        MANDATORY_FAILURES=$((MANDATORY_FAILURES + 1))
      fi
      ;;
    SKIP) SKIPPED=$((SKIPPED + 1));;
  esac

  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$status" "$stage" "$id" "$mandatory" \
    "$(sanitize_field "$description")" "$(sanitize_field "$detail")" >> "$TMP_RESULTS"

  local marker color
  case "$status" in
    PASS) marker="PASS"; color="$C_GREEN";;
    FAIL) marker="FAIL"; color="$C_RED";;
    WARN) marker="WARN"; color="$C_YELLOW";;
    SKIP) marker="SKIP"; color="$C_BLUE";;
  esac
  printf '%s[%s]%s %-10s %-32s %s\n' "$color" "$marker" "$C_RESET" "$stage" "$id" "$description"
  if [[ "$VERBOSE" -eq 1 && -n "$detail" ]]; then
    printf '  %s\n' "$detail"
  fi
}

run_test_script() {
  local stage="$1" id="$2" mandatory="$3" path="$4" description="$5"
  local full="$REPO/$path"
  if [[ ! -f "$full" ]]; then
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "ausente: $path"
    return
  fi
  if [[ ! -x "$full" ]]; then
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "não executável: $path"
    return
  fi

  local out rc
  out="$(mktemp)"
  set +e
  (cd "$REPO" && "$full") >"$out" 2>&1
  rc=$?
  set -e

  if [[ "$rc" -eq 0 ]]; then
    record_result PASS "$stage" "$id" "$mandatory" "$description" "script=$path"
  else
    local tail_out
    tail_out="$(tail -n 12 "$out" | tr '\n' ' ' | cut -c1-1200)"
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "rc=$rc; $tail_out"
  fi

  if [[ "$VERBOSE" -eq 1 ]]; then
    sed 's/^/    /' "$out"
  fi
  rm -f "$out"
}

check_file() {
  local stage="$1" id="$2" mandatory="$3" path="$4" description="$5"
  if [[ -f "$REPO/$path" ]]; then
    record_result PASS "$stage" "$id" "$mandatory" "$description" "$path"
  else
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "ausente: $path"
  fi
}

check_dir() {
  local stage="$1" id="$2" mandatory="$3" path="$4" description="$5"
  if [[ -d "$REPO/$path" ]]; then
    record_result PASS "$stage" "$id" "$mandatory" "$description" "$path"
  else
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "ausente: $path"
  fi
}

check_any_match() {
  local stage="$1" id="$2" mandatory="$3" regex="$4" description="$5"
  local found
  found="$(cd "$REPO" && find . -type f -print | sed 's#^\./##' | grep -E "$regex" | head -n 1 || true)"
  if [[ -n "$found" ]]; then
    record_result PASS "$stage" "$id" "$mandatory" "$description" "$found"
  else
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "nenhum arquivo corresponde a: $regex"
  fi
}

check_min_count() {
  local stage="$1" id="$2" mandatory="$3" dir="$4" regex="$5" minimum="$6" description="$7"
  local count=0
  if [[ -d "$REPO/$dir" ]]; then
    count="$(cd "$REPO/$dir" && find . -type f -print | grep -E "$regex" | wc -l | tr -d ' ')"
  fi
  if (( count >= minimum )); then
    record_result PASS "$stage" "$id" "$mandatory" "$description" "quantidade=$count; mínimo=$minimum"
  else
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "quantidade=$count; mínimo=$minimum; diretório=$dir"
  fi
}

check_regex_present() {
  local stage="$1" id="$2" mandatory="$3" path="$4" regex="$5" description="$6"
  if [[ ! -e "$REPO/$path" ]]; then
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "caminho ausente: $path"
    return
  fi
  if grep -R -n -E --exclude-dir=.git --exclude-dir=build -- "$regex" "$REPO/$path" >/tmp/sister_gate_grep.$$ 2>/dev/null; then
    local first
    first="$(head -n 1 /tmp/sister_gate_grep.$$ | sed "s#${REPO}/##")"
    rm -f /tmp/sister_gate_grep.$$
    record_result PASS "$stage" "$id" "$mandatory" "$description" "$first"
  else
    rm -f /tmp/sister_gate_grep.$$
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "padrão não encontrado: $regex"
  fi
}

check_regex_absent() {
  local stage="$1" id="$2" mandatory="$3" path="$4" regex="$5" description="$6"
  if [[ ! -e "$REPO/$path" ]]; then
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "caminho ausente: $path"
    return
  fi
  if grep -R -n -E --exclude-dir=.git --exclude-dir=build -- "$regex" "$REPO/$path" >/tmp/sister_gate_grep.$$ 2>/dev/null; then
    local first
    first="$(head -n 1 /tmp/sister_gate_grep.$$ | sed "s#${REPO}/##")"
    rm -f /tmp/sister_gate_grep.$$
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "encontrado: $first"
  else
    rm -f /tmp/sister_gate_grep.$$
    record_result PASS "$stage" "$id" "$mandatory" "$description" "padrão ausente"
  fi
}

check_approval() {
  local stage="$1" id="$2" mandatory="$3" path="$4" description="$5"
  if [[ ! -f "$REPO/$path" ]]; then
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "ausente: $path"
    return
  fi
  if grep -Eiq '^[[:space:]]*status[[:space:]]*:[[:space:]]*(approved|aprovado)[[:space:]]*$' "$REPO/$path"; then
    record_result PASS "$stage" "$id" "$mandatory" "$description" "$path"
  else
    record_result FAIL "$stage" "$id" "$mandatory" "$description" "o arquivo não contém status: approved/aprovado"
  fi
}

check_git_repo() {
  if git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    record_result PASS pre-alpha git-repository yes "Repositório Git reconhecido" "$(git -C "$REPO" rev-parse --show-toplevel)"
  else
    record_result FAIL pre-alpha git-repository yes "Repositório Git reconhecido" "não é um repositório Git"
  fi
}

check_git_clean() {
  local mandatory="no"
  [[ "$MODE" == "certify" ]] && mandatory="yes"
  local dirty_output
  dirty_output="$(git -C "$REPO" status --porcelain --untracked-files=normal 2>/dev/null || true)"
  if [[ "$INITIAL_GIT_DIRTY" == "false" ]]; then
    record_result PASS pre-alpha git-clean "$mandatory" "Árvore Git limpa para atestação" "clean"
  elif [[ "$MODE" == "certify" ]]; then
    record_result FAIL pre-alpha git-clean yes "Árvore Git limpa para atestação" "$(printf '%s' "$dirty_output" | head -n 10 | tr '\n' ' ')"
  else
    record_result WARN pre-alpha git-clean no "Árvore Git limpa para atestação" "há alterações locais; permitido apenas em modo check"
  fi
}

check_no_tracked_secrets() {
  local suspicious
  suspicious="$(git -C "$REPO" ls-files 2>/dev/null | \
    grep -Ei '(^|/)(\.env($|\.)|.*\.(pem|key|p12|pfx)$|id_rsa$|credentials?($|\.)|secrets?($|\.))' | \
    grep -Evi '(^|/)\.env([.][^.]+)*[.]example$' || true)"
  if [[ -z "$suspicious" ]]; then
    record_result PASS pre-alpha tracked-secrets yes "Nenhum arquivo de segredo óbvio está versionado" "nenhum nome suspeito"
  else
    record_result FAIL pre-alpha tracked-secrets yes "Nenhum arquivo de segredo óbvio está versionado" "$(printf '%s' "$suspicious" | tr '\n' ' ')"
  fi
}

check_runtime_url() {
  local stage="$1" id="$2" url="$3" expected="$4" description="$5"
  if [[ "$RUNTIME_CHECKS" -eq 0 ]]; then
    record_result SKIP "$stage" "$id" no "$description" "use --runtime"
    return
  fi
  if ! command -v curl >/dev/null 2>&1; then
    record_result FAIL "$stage" "$id" yes "$description" "curl não encontrado"
    return
  fi
  local body status
  body="$(mktemp)"
  set +e
  status="$(curl --silent --show-error --max-time 10 --output "$body" --write-out '%{http_code}' "$url")"
  local rc=$?
  set -e
  if [[ "$rc" -eq 0 && "$status" =~ ^2[0-9][0-9]$ ]] && grep -Eiq "$expected" "$body"; then
    record_result PASS "$stage" "$id" yes "$description" "url=$url; http=$status"
  else
    local excerpt
    excerpt="$(head -c 500 "$body" | tr '\n' ' ')"
    record_result FAIL "$stage" "$id" yes "$description" "url=$url; rc=$rc; http=$status; body=$excerpt"
  fi
  rm -f "$body"
}

check_stable_tag() {
  local tag
  tag="$(git -C "$REPO" describe --tags --exact-match 2>/dev/null || true)"
  if [[ "$tag" =~ ^v?([1-9][0-9]*|0)\.([0-9]+)\.([0-9]+)$ ]]; then
    record_result PASS production stable-tag yes "Commit está marcado com versão SemVer estável" "$tag"
  else
    record_result FAIL production stable-tag yes "Commit está marcado com versão SemVer estável" "tag atual='$tag'"
  fi
}

check_signed_tag() {
  if [[ "$REQUIRE_SIGNED_TAG" -ne 1 ]]; then
    record_result SKIP production signed-tag no "Tag de produção assinada" "REQUIRE_SIGNED_TAG=0"
    return
  fi
  local tag
  tag="$(git -C "$REPO" describe --tags --exact-match 2>/dev/null || true)"
  if [[ -n "$tag" ]] && git -C "$REPO" tag -v "$tag" >/tmp/sister_tag_verify.$$ 2>&1; then
    record_result PASS production signed-tag yes "Tag de produção assinada" "$tag"
  else
    local detail
    detail="$(tail -n 8 /tmp/sister_tag_verify.$$ 2>/dev/null | tr '\n' ' ' || true)"
    rm -f /tmp/sister_tag_verify.$$
    record_result FAIL production signed-tag yes "Tag de produção assinada" "$detail"
    return
  fi
  rm -f /tmp/sister_tag_verify.$$
}

load_config() {
  [[ -f "$CONFIG_FILE" ]] || return 0

  local line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "${line//[[:space:]]/}" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" == *=* ]] || die "linha inválida em $CONFIG_FILE: $line"
    key="${line%%=*}"
    value="${line#*=}"
    key="${key//[[:space:]]/}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ "$value" =~ ^\".*\"$ || "$value" =~ ^\'.*\'$ ]]; then
      value="${value:1:${#value}-2}"
    fi
    case "$key" in
      VERIFY_IDENTICAL|SMOKE_TEST|UNIT_TEST|CONTRACT_TEST|INTEGRATION_TEST|SECURITY_TEST|LOAD_TEST|RECOVERY_TEST|BACKUP_RESTORE_TEST|KEY_ROTATION_TEST|ROLLBACK_TEST|GATEWAY_VALIDATE|BASE_URL|CLIMA_HEALTH_URL|NEXO_HEALTH_URL|MIN_RUNBOOKS|REQUIRE_SIGNED_TAG)
        printf -v "$key" '%s' "$value"
        ;;
      *) die "chave não permitida em $CONFIG_FILE: $key";;
    esac
  done < "$CONFIG_FILE"
}

init_layout() {
  local root="$REPO"
  mkdir -p "$root/.sister/attestations" \
           "$root/docs/evidence/pre-alpha" \
           "$root/docs/evidence/alpha" \
           "$root/docs/evidence/beta" \
           "$root/docs/evidence/gamma" \
           "$root/docs/evidence/production"

  if [[ ! -f "$root/.sister/status.yml" ]]; then
    cat > "$root/.sister/status.yml" <<'EOF'
system: sister
stage: development_prototype
production_ready: false
functional_flow_validated: true
EOF
  fi

  if [[ ! -f "$root/.sister/maturity.conf" ]]; then
    cat > "$root/.sister/maturity.conf" <<'EOF'
# Caminhos relativos à raiz do repositório.
VERIFY_IDENTICAL=scripts/verify-identical.sh
SMOKE_TEST=scripts/ci/test-smoke.sh
UNIT_TEST=scripts/ci/test-unit.sh
CONTRACT_TEST=scripts/ci/test-contract.sh
INTEGRATION_TEST=scripts/ci/test-integration.sh
SECURITY_TEST=scripts/ci/test-security.sh
LOAD_TEST=scripts/ci/test-load.sh
RECOVERY_TEST=scripts/ci/test-recovery.sh
BACKUP_RESTORE_TEST=scripts/ci/test-backup-restore.sh
KEY_ROTATION_TEST=scripts/ci/test-key-rotation.sh
ROLLBACK_TEST=scripts/ci/test-rollback.sh
GATEWAY_VALIDATE=scripts/ci/validate-gateway.sh

BASE_URL=http://127.0.0.1:8000
CLIMA_HEALTH_URL=http://127.0.0.1:8501/_sister/health
NEXO_HEALTH_URL=http://127.0.0.1:8015/_sister/health

MIN_RUNBOOKS=10
REQUIRE_SIGNED_TAG=0
EOF
  fi

  cat > "$root/docs/evidence/README.md" <<'EOF'
# Evidências dos gates de maturidade

Os arquivos deste diretório registram aprovações e evidências humanas que não
podem ser inferidas somente pelo código. Uma aprovação deve conter, no mínimo:

```yaml
stage: gamma
area: security
status: approved
commit: <sha completo>
approved_by: <nome ou papel>
approved_at: <data ISO-8601>
evidence:
  - <relatório, teste ou decisão>
notes: <ressalvas>
```

O verificador não cria aprovações. Ele apenas comprova que o arquivo exigido
existe e contém `status: approved` ou `status: aprovado`.
EOF

  printf 'Estrutura inicial criada em %s\n' "$root"
  printf 'Nenhum teste ou aceite foi criado automaticamente.\n'
}

run_pre_alpha() {
  check_git_repo
  check_git_clean
  check_no_tracked_secrets

  run_test_script pre-alpha baseline-integrity yes "$VERIFY_IDENTICAL" \
    "Snapshot/baseline permanece íntegro"
  run_test_script pre-alpha smoke-flow yes "$SMOKE_TEST" \
    "Smoke tests preservam autenticação, Nexo e Clima"

  check_any_match pre-alpha transition-plan yes \
    '(^|/)(docs/.*)?sister.*transi(c|ç)(a|ã)o.*prototipo.*\.(md|tex)$' \
    "Plano de transição está versionado"
  check_any_match pre-alpha maturity-roadmap yes \
    '(^|/)(docs/.*)?sister.*(alfa|alpha).*beta.*(gama|gamma).*\.(md|tex)$' \
    "Roteiro Alfa–Beta–Gama está versionado"
  check_file pre-alpha status-file yes .sister/status.yml \
    "Arquivo formal de estado do SisTer existe"
  check_regex_present pre-alpha prototype-status yes .sister/status.yml \
    'stage[[:space:]]*:[[:space:]]*(development_prototype|development_provisional|pre-alpha)|production_ready[[:space:]]*:[[:space:]]*false' \
    "Estado provisório está declarado"
}

run_alpha() {
  check_dir alpha contract-dir yes contracts/subsystem/1.0.0 \
    "Contrato sister.subsystem/1.0.0 existe"
  for file in manifest.schema.json capabilities.schema.json identity-claims.schema.json health.schema.json readiness.schema.json error.schema.json audit-event.schema.json openapi.yaml README.md; do
    check_file alpha "contract-$(check_id_slug "$file")" yes \
      "contracts/subsystem/1.0.0/$file" "Artefato contratual $file existe"
  done

  check_min_count alpha adrs yes docs/adr \
    'ADR-[0-9]{4}.*\.(md|adoc|txt)$' 7 \
    "ADRs arquiteturais mínimos estão registrados"

  check_any_match alpha migration-users yes \
    '(^|/)storage/migrations/.*user.*\.sql$' "Migração de usuários existe"
  check_any_match alpha migration-sessions yes \
    '(^|/)storage/migrations/.*session.*\.sql$' "Migração de sessões existe"
  check_any_match alpha migration-capabilities yes \
    '(^|/)storage/migrations/.*capabilit.*\.sql$' "Migração de capacidades existe"

  check_regex_present alpha token-hash yes apps \
    'token_hash|session_token_hash' "Sessões armazenam hash do token"
  check_regex_present alpha signed-identity yes apps \
    'audience|["'\'']aud["'\'']|token_issuer|signing_key|kid' \
    "Código contém emissão/validação de identidade assinada"
  check_regex_present alpha capability-api yes apps \
    '/api/me/capabilities|me/capabilities' \
    "API de capacidades do usuário está implementada"

  run_test_script alpha unit-tests yes "$UNIT_TEST" "Testes unitários aprovados"
  run_test_script alpha contract-tests yes "$CONTRACT_TEST" "Testes de contrato aprovados"

  check_approval alpha architecture-approval yes \
    docs/evidence/alpha/architecture.md "Arquitetura Alfa aprovada"
  check_approval alpha security-approval yes \
    docs/evidence/alpha/security.md "Segurança Alfa aprovada"
}

run_beta() {
  check_dir beta gateway-config yes gateway/config "Configuração do gateway existe"
  run_test_script beta gateway-validation yes "$GATEWAY_VALIDATE" \
    "Configuração do gateway é válida"

  check_dir beta clima-adapter yes adapters/clima-reference \
    "Adaptador de referência do Clima existe"
  check_dir beta nexo-adapter yes adapters/nexo-reference \
    "Adaptador de referência do Nexo existe"

  check_any_match beta registry-migration yes \
    '(^|/)storage/migrations/.*(registry|subsystem).*\.sql$' \
    "Migração do registry de subsistemas existe"

  check_regex_absent beta no-artisanal-websocket yes apps/sisterd \
    'openWebSocketProxy|tunnelSockets[[:space:]]*\(' \
    "Túnel WebSocket artesanal foi removido do sisterd"
  check_regex_absent beta no-cookie-forwarding yes apps/sisterd \
    'Cookie:[^"\n]*(sister_session|SISTER_SESSION)|sister_session[^"\n]*Cookie:' \
    "Cookie do navegador não é encaminhado pelo sisterd"
  check_regex_absent beta no-specific-ports yes apps/sisterd \
    'climaPort|nexoPort|SISTER_CLIMA_PORT|SISTER_NEXO_PORT' \
    "Portas específicas de Clima/Nexo saíram do núcleo"
  check_regex_absent beta no-specific-routes yes apps/sisterd \
    '/integrations/(clima|nexo)' \
    "Rotas específicas de Clima/Nexo saíram do núcleo"

  run_test_script beta integration-tests yes "$INTEGRATION_TEST" \
    "Testes de integração aprovados"
  run_test_script beta contract-tests yes "$CONTRACT_TEST" \
    "Clima e Nexo passam na suíte comum de conformidade"
  run_test_script beta rollback-tests yes "$ROLLBACK_TEST" \
    "Rollback do caminho novo foi ensaiado"

  check_runtime_url beta sister-health "$BASE_URL/api/health" \
    '"status"[[:space:]]*:[[:space:]]*"ok"' "sisterd responde ao health"
  check_runtime_url beta clima-health "$CLIMA_HEALTH_URL" \
    'sister_clima|Sister-Clima|"status"' "Clima responde ao contrato de health"
  check_runtime_url beta nexo-health "$NEXO_HEALTH_URL" \
    'sister_nexo|SisTer Nexo|"status"' "Nexo responde ao contrato de health"

  check_approval beta architecture-approval yes \
    docs/evidence/beta/architecture.md "Arquitetura Beta aprovada"
  check_approval beta domain-approval yes \
    docs/evidence/beta/domains.md "Responsáveis de Clima e Nexo aprovaram a Beta"
}

run_gamma() {
  check_dir gamma observability yes observability \
    "Artefatos de observabilidade existem"
  check_any_match gamma metrics-config yes \
    '(^|/)(observability|deploy)/.*(metric|prometheus|dashboard).*\.(ya?ml|json|md)$' \
    "Métricas ou dashboards estão versionados"
  check_any_match gamma audit-migration yes \
    '(^|/)storage/migrations/.*audit.*\.sql$' \
    "Persistência de auditoria possui migração"

  check_dir gamma systemd-units yes deploy/systemd \
    "Unidades systemd estão versionadas"
  check_regex_present gamma systemd-hardening yes deploy/systemd \
    'NoNewPrivileges[[:space:]]*=[[:space:]]*yes|ProtectSystem[[:space:]]*=[[:space:]]*strict' \
    "Hardening systemd está presente"

  run_test_script gamma security-tests yes "$SECURITY_TEST" \
    "Testes de segurança aprovados"
  run_test_script gamma load-tests yes "$LOAD_TEST" \
    "Testes de carga e isolamento aprovados"
  run_test_script gamma recovery-tests yes "$RECOVERY_TEST" \
    "Testes de falha e recuperação aprovados"
  run_test_script gamma backup-restore yes "$BACKUP_RESTORE_TEST" \
    "Backup e restauração foram testados"
  run_test_script gamma key-rotation yes "$KEY_ROTATION_TEST" \
    "Rotação de chaves foi testada"
  run_test_script gamma rollback-tests yes "$ROLLBACK_TEST" \
    "Rollback de release foi testado"

  check_min_count gamma runbooks yes docs/runbooks \
    '.*\.(md|adoc|txt)$' "$MIN_RUNBOOKS" \
    "Quantidade mínima de runbooks foi atingida"

  check_file gamma risk-register yes docs/threat-model/risk-register.md \
    "Registro de riscos existe"
  check_regex_absent gamma no-open-critical-risks yes docs/threat-model/risk-register.md \
    '(critical|crítico)[^[:cntrl:]]*(open|aberto)|(open|aberto)[^[:cntrl:]]*(critical|crítico)' \
    "Não há risco crítico marcado como aberto"

  check_approval gamma architecture-approval yes \
    docs/evidence/gamma/architecture.md "Arquitetura Gama aprovada"
  check_approval gamma security-approval yes \
    docs/evidence/gamma/security.md "Segurança Gama aprovada"
  check_approval gamma quality-approval yes \
    docs/evidence/gamma/quality.md "Qualidade Gama aprovada"
  check_approval gamma operations-approval yes \
    docs/evidence/gamma/operations.md "Operação Gama aprovada"
  check_approval gamma domains-approval yes \
    docs/evidence/gamma/domains.md "Domínios Gama aprovados"
}

run_production() {
  check_stable_tag
  check_signed_tag

  check_any_match production release-manifest yes \
    '(^|/)release/.*(manifest|checksums|sha256).*\.(json|txt|sha256)$' \
    "Manifesto/checksums da release existem"
  check_regex_absent production no-legacy-proxy-apps yes apps \
    'legacy_proxy[[:space:]]*:[[:space:]]*(enabled|true)|browser_cookie_forwarded[[:space:]]*:[[:space:]]*true' \
    "Caminho legado não permanece habilitado no código"
  check_regex_absent production no-legacy-proxy-gateway yes gateway \
    'legacy_proxy[[:space:]]*:[[:space:]]*(enabled|true)|browser_cookie_forwarded[[:space:]]*:[[:space:]]*true' \
    "Caminho legado não permanece habilitado no gateway"
  check_approval production final-approval yes \
    docs/evidence/production/release.md "Promoção para produção aprovada"
  run_test_script production smoke-tests yes "$SMOKE_TEST" \
    "Smoke tests da release de produção aprovados"
}

write_markdown_report() {
  local destination="$1"
  local commit branch dirty generated result
  commit="$(git -C "$REPO" rev-parse HEAD 2>/dev/null || printf unknown)"
  branch="$(git -C "$REPO" branch --show-current 2>/dev/null || printf detached)"
  dirty="$INITIAL_GIT_DIRTY"
  generated="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  result="PASS"
  (( MANDATORY_FAILURES > 0 )) && result="FAIL"
  if [[ "$STRICT" -eq 1 && "$WARNED" -gt 0 ]]; then result="FAIL"; fi

  {
    printf '# SisTer — Relatório do Gate %s\n\n' "$TARGET_STAGE"
    printf -- '- **Resultado:** `%s`\n' "$result"
    printf -- '- **Gerado em:** `%s`\n' "$generated"
    printf -- '- **Repositório:** `%s`\n' "$REPO"
    printf -- '- **Commit:** `%s`\n' "$commit"
    printf -- '- **Branch:** `%s`\n' "$branch"
    printf -- '- **Árvore suja:** `%s`\n' "$dirty"
    printf -- '- **Verificador:** `%s`\n' "$SCRIPT_VERSION"
    printf -- '- **Total:** %d; **PASS:** %d; **FAIL:** %d; **WARN:** %d; **SKIP:** %d\n\n' \
      "$TOTAL" "$PASSED" "$FAILED" "$WARNED" "$SKIPPED"
    printf '| Estado | Estágio | Check | Obrigatório | Descrição | Evidência/erro |\n'
    printf '|---|---|---|---|---|---|\n'
    while IFS=$'\t' read -r status stage id mandatory description detail; do
      detail="${detail//|/\\|}"
      description="${description//|/\\|}"
      printf '| %s | %s | `%s` | %s | %s | %s |\n' \
        "$status" "$stage" "$id" "$mandatory" "$description" "$detail"
    done < "$TMP_RESULTS"
    printf '\n> Esta evidência atesta que os checks configurados passaram no commit indicado. '
    printf 'Ela não substitui revisão independente nem aceite dos responsáveis.\n'
  } > "$destination"
}

write_attestation() {
  local destination="$1"
  command -v python3 >/dev/null 2>&1 || die "python3 é necessário para gerar a atestação JSON"

  local commit branch dirty generated script_hash config_hash result
  commit="$(git -C "$REPO" rev-parse HEAD)"
  branch="$(git -C "$REPO" branch --show-current || true)"
  dirty="$INITIAL_GIT_DIRTY"
  generated="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  script_hash="$(sha256_file "$0")"
  config_hash="none"
  [[ -f "$CONFIG_FILE" ]] && config_hash="$(sha256_file "$CONFIG_FILE")"
  result="PASS"
  (( MANDATORY_FAILURES > 0 )) && result="FAIL"
  if [[ "$STRICT" -eq 1 && "$WARNED" -gt 0 ]]; then result="FAIL"; fi

  mkdir -p "$(dirname "$destination")"
  python3 - "$TMP_RESULTS" "$destination" <<PY
import csv, json, platform, socket, sys
from pathlib import Path

rows_path, destination = sys.argv[1], sys.argv[2]
checks = []
with open(rows_path, encoding="utf-8", newline="") as f:
    for status, stage, check_id, mandatory, description, detail in csv.reader(f, delimiter="\t"):
        checks.append({
            "status": status,
            "stage": stage,
            "id": check_id,
            "mandatory": mandatory == "yes",
            "description": description,
            "detail": detail,
        })

payload = {
    "schema": "sister.maturity-attestation/1.0.0",
    "project": "SisTer",
    "stage": ${TARGET_STAGE@Q},
    "result": ${result@Q},
    "generated_at": ${generated@Q},
    "repository": ${REPO@Q},
    "git": {
        "commit": ${commit@Q},
        "branch": ${branch@Q},
        "dirty": ${dirty@Q} == "true",
    },
    "verifier": {
        "version": ${SCRIPT_VERSION@Q},
        "script_sha256": ${script_hash@Q},
        "config_sha256": ${config_hash@Q},
    },
    "environment": {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": platform.python_version(),
    },
    "summary": {
        "total": ${TOTAL},
        "passed": ${PASSED},
        "failed": ${FAILED},
        "warned": ${WARNED},
        "skipped": ${SKIPPED},
        "mandatory_failures": ${MANDATORY_FAILURES},
    },
    "checks": checks,
    "disclaimer": (
        "A atestação comprova a execução dos checks configurados no commit indicado; "
        "não substitui revisão técnica, de segurança ou aceite humano."
    ),
}
Path(destination).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

  if [[ -n "$GPG_KEY" ]]; then
    command -v gpg >/dev/null 2>&1 || die "gpg não encontrado"
    gpg --batch --yes --local-user "$GPG_KEY" --armor --detach-sign "$destination"
  fi
}

write_status_json() {
  local destination="$1"
  local commit branch generated result
  commit="$(git -C "$REPO" rev-parse HEAD 2>/dev/null || printf unknown)"
  branch="$(git -C "$REPO" branch --show-current 2>/dev/null || printf detached)"
  generated="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  result="PASS"
  (( MANDATORY_FAILURES > 0 )) && result="FAIL"
  if [[ "$STRICT" -eq 1 && "$WARNED" -gt 0 ]]; then result="FAIL"; fi

  local python_args=(
    "--results" "$TMP_RESULTS"
    "--destination" "$destination"
    "--repository" "$REPO"
    "--target-stage" "$TARGET_STAGE"
    "--result" "$result"
    "--generated-at" "$generated"
    "--verifier-version" "$SCRIPT_VERSION"
    "--commit" "$commit"
    "--branch" "${branch:-detached}"
    "--dirty" "$INITIAL_GIT_DIRTY"
    "--total" "$TOTAL"
    "--passed" "$PASSED"
    "--failed" "$FAILED"
    "--warned" "$WARNED"
    "--skipped" "$SKIPPED"
    "--mandatory-failures" "$MANDATORY_FAILURES"
    "--engine" "$ENGINE"
    "--engine-mode" "$MODE"
    "--engine-version" "$SCRIPT_VERSION"
  )
  
  if [[ "$ENGINE" == "compare" ]]; then
    python_args+=("--compare-performed" "true" "--compare-equivalent" "true")
  fi
  
  python3 "$REPO/scripts/maturity/sanitize-attestation.py" "${python_args[@]}"
}

parse_args() {
  local init=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --stage) TARGET_STAGE="${2:-}"; shift 2;;
      --mode) MODE="${2:-}"; shift 2;;
      --repo) REPO="${2:-}"; shift 2;;
      --config) CONFIG_FILE="${2:-}"; shift 2;;
      --report) REPORT_FILE="${2:-}"; shift 2;;
      --attestation) ATTESTATION_FILE="${2:-}"; shift 2;;
      --status-json) STATUS_JSON_FILE="${2:-}"; shift 2;;
      --engine) ENGINE="${2:-}"; shift 2;;
      --gpg-key) GPG_KEY="${2:-}"; shift 2;;
      --runtime) RUNTIME_CHECKS=1; shift;;
      --strict) STRICT=1; shift;;
      --verbose) VERBOSE=1; shift;;
      --no-color) NO_COLOR=1; shift;;
      --init) init=1; shift;;
      -h|--help) usage; exit 0;;
      *) die "opção desconhecida: $1";;
    esac
  done

  if [[ -z "$REPO" ]]; then
    REPO="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  fi
  REPO="$(cd "$REPO" && pwd)"
  [[ -n "$CONFIG_FILE" ]] || CONFIG_FILE="$REPO/.sister/maturity.conf"

  if [[ "$init" -eq 1 ]]; then
    init_layout
    exit 0
  fi

  [[ -n "$TARGET_STAGE" ]] || die "--stage é obrigatório"
  [[ -n "${STAGE_RANK[$TARGET_STAGE]+x}" ]] || die "estágio inválido: $TARGET_STAGE"
  [[ "$MODE" == "check" || "$MODE" == "certify" ]] || die "modo inválido: $MODE"
  [[ "$ENGINE" == "legacy" || "$ENGINE" == "declarative" || "$ENGINE" == "compare" ]] || die "motor inválido: $ENGINE"
  
  export MODE
}

main() {
  parse_args "$@"
  color_init
  load_config

  INITIAL_GIT_DIRTY="false"
  [[ -n "$(git -C "$REPO" status --porcelain --untracked-files=normal 2>/dev/null || true)" ]] && INITIAL_GIT_DIRTY="true"

  TMP_RESULTS="$(mktemp)"
  trap 'rm -f "${TMP_RESULTS:-}"' EXIT

  printf '%sSisTer maturity gates%s — estágio alvo: %s%s%s — modo: %s\n\n' \
    "$C_BOLD" "$C_RESET" "$C_BOLD" "$TARGET_STAGE" "$C_RESET" "$MODE"

  if [[ "$ENGINE" == "legacy" ]]; then
    stage_enabled pre-alpha && run_pre_alpha
    stage_enabled alpha && run_alpha
    stage_enabled beta && run_beta
    stage_enabled gamma && run_gamma
    stage_enabled production && run_production
  elif [[ "$ENGINE" == "declarative" ]]; then
    local strict_flag=""
    [[ "$STRICT" -eq 1 ]] && strict_flag="--strict"
    local json_out
    if ! json_out="$(python3 "$REPO/scripts/maturity/evaluator.py" --repo "$REPO" --profile "engineering/maturity/profiles/sister-core.yaml" --stage "$TARGET_STAGE" $strict_flag)"; then
       die "Falha ao executar evaluator.py: $json_out"
    fi
    mkdir -p "$REPO/.run/maturity"
    printf "%s\n" "$json_out" > "$REPO/.run/maturity/execution-plan.json"
    
    while IFS=$'\t' read -r status stage id mandatory description detail; do
      record_result "$status" "$stage" "$id" "$mandatory" "$description" "$detail"
    done < <(python3 "$REPO/scripts/maturity/json-to-tabular.py" "$REPO/.run/maturity/execution-plan.json")
  elif [[ "$ENGINE" == "compare" ]]; then
    # Run legacy silently
    local original_verbose="$VERBOSE"
    VERBOSE=0
    local legacy_results="$(mktemp)"
    local old_tmp="$TMP_RESULTS"
    TMP_RESULTS="$legacy_results"
    
    # Save legacy counters
    local old_total=$TOTAL
    local old_passed=$PASSED
    local old_failed=$FAILED
    local old_warned=$WARNED
    local old_skipped=$SKIPPED
    local old_mandatory=$MANDATORY_FAILURES
    TOTAL=0; PASSED=0; FAILED=0; WARNED=0; SKIPPED=0; MANDATORY_FAILURES=0
    
    # Supress stdout for legacy
    {
      stage_enabled pre-alpha && run_pre_alpha
      stage_enabled alpha && run_alpha
      stage_enabled beta && run_beta
      stage_enabled gamma && run_gamma
      stage_enabled production && run_production
    } >/dev/null 2>&1
    
    local legacy_total=$TOTAL
    local legacy_passed=$PASSED
    
    # Restore counters for declarative
    TOTAL=$old_total; PASSED=$old_passed; FAILED=$old_failed; WARNED=$old_warned; SKIPPED=$old_skipped; MANDATORY_FAILURES=$old_mandatory
    TMP_RESULTS="$old_tmp"
    VERBOSE="$original_verbose"
    
    # Run declarative normally
    local strict_flag=""
    [[ "$STRICT" -eq 1 ]] && strict_flag="--strict"
    local json_out
    if ! json_out="$(python3 "$REPO/scripts/maturity/evaluator.py" --repo "$REPO" --profile "engineering/maturity/profiles/sister-core.yaml" --stage "$TARGET_STAGE" $strict_flag)"; then
       die "Falha ao executar evaluator.py: $json_out"
    fi
    mkdir -p "$REPO/.run/maturity"
    printf "%s\n" "$json_out" > "$REPO/.run/maturity/execution-plan.json"
    
    local decl_results="$(mktemp)"
    while IFS=$'\t' read -r status stage id mandatory description detail; do
      record_result "$status" "$stage" "$id" "$mandatory" "$description" "$detail"
      printf '%s\t%s\t%s\t%s\t%s\n' "$status" "$stage" "$id" "$mandatory" "$description" >> "$decl_results"
    done < <(python3 "$REPO/scripts/maturity/json-to-tabular.py" "$REPO/.run/maturity/execution-plan.json")
    
    local legacy_cleaned="$(mktemp)"
    awk -F'\t' '{print $1"\t"$2"\t"$3"\t"$4"\t"$5}' "$legacy_results" > "$legacy_cleaned"
    
    printf "\n%s--- Comparação de Motores ---%s\n" "$C_BOLD" "$C_RESET"
    if cmp -s "$legacy_cleaned" "$decl_results"; then
      printf "%sEquivalência comprovada.%s\n" "$C_GREEN" "$C_RESET"
    else
      printf "%sDiscrepância detectada entre legacy e declarative!%s\n" "$C_RED" "$C_RESET"
      diff -u "$legacy_cleaned" "$decl_results" || true
      die "Os motores divergiram. Verifique o plano."
    fi
    
    rm -f "$legacy_results" "$decl_results" "$legacy_cleaned"
  fi

  local result="PASS"
  if (( MANDATORY_FAILURES > 0 )); then result="FAIL"; fi
  if [[ "$STRICT" -eq 1 && "$WARNED" -gt 0 ]]; then result="FAIL"; fi

  printf '\n%sResumo%s: total=%d pass=%d fail=%d warn=%d skip=%d mandatory_failures=%d\n' \
    "$C_BOLD" "$C_RESET" "$TOTAL" "$PASSED" "$FAILED" "$WARNED" "$SKIPPED" "$MANDATORY_FAILURES"

  if [[ -n "$REPORT_FILE" ]]; then
    mkdir -p "$(dirname "$REPORT_FILE")"
    write_markdown_report "$REPORT_FILE"
    printf 'Relatório: %s\n' "$REPORT_FILE"
  fi

  if [[ -n "$STATUS_JSON_FILE" ]]; then
    write_status_json "$STATUS_JSON_FILE"
    printf 'Status JSON: %s\n' "$STATUS_JSON_FILE"
  fi

  if [[ "$MODE" == "certify" ]]; then
    if [[ "$result" != "PASS" ]]; then
      printf '%sAtestação não gerada: há falhas obrigatórias.%s\n' "$C_RED" "$C_RESET" >&2
      exit 1
    fi
    if [[ -z "$ATTESTATION_FILE" ]]; then
      local commit_short
      commit_short="$(git -C "$REPO" rev-parse --short=12 HEAD)"
      ATTESTATION_FILE="$REPO/.sister/attestations/${TARGET_STAGE}-${commit_short}.json"
    fi
    write_attestation "$ATTESTATION_FILE"
    printf 'Atestação: %s\n' "$ATTESTATION_FILE"
    [[ -n "$GPG_KEY" ]] && printf 'Assinatura: %s.asc\n' "$ATTESTATION_FILE"
  fi

  if [[ "$result" == "PASS" ]]; then
    printf '%sGATE %s: APROVADO%s\n' "$C_GREEN" "$TARGET_STAGE" "$C_RESET"
    exit 0
  fi

  printf '%sGATE %s: REPROVADO%s\n' "$C_RED" "$TARGET_STAGE" "$C_RESET"
  exit 1
}

main "$@"
