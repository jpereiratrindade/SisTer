const STAGE_LABELS = {
  "pre-alpha": "Pré-Alfa",
  alpha: "Alfa",
  beta: "Beta",
  gamma: "Gama",
  production: "Produção",
};

const STATUS_LABELS = {
  PASS: "Aprovado",
  FAIL: "Falhou",
  WARN: "Advertência",
  SKIP: "Ignorado",
};

const STAGE_STATE_LABELS = {
  approved: "Aprovado",
  in_progress: "Em andamento",
  blocked: "Bloqueado",
  not_started: "Não iniciado",
};

const ENGINEERING_DIMENSIONS = [
  { id: "architecture", label: "Arquitetura", patterns: ["architecture", "arquitet", "roadmap", "transition", "baseline"] },
  { id: "security", label: "Segurança", patterns: ["security", "secret", "identity", "identidade", "auth", "assin"] },
  { id: "tests", label: "Testes", patterns: ["test", "smoke", "verify", "quality"] },
  { id: "docs", label: "Documentação", patterns: ["doc", "adr", "roadmap", "plan"] },
  { id: "contracts", label: "Contratos", patterns: ["contract", "contrato", "schema"] },
  { id: "observability", label: "Observabilidade", patterns: ["health", "observ", "status", "provenance", "proveni"] },
];

const SUBSYSTEMS = [
  { id: "sister-core", label: "SisTer-Core", patterns: ["repository", "baseline", "status-file", "prototype-status", "git-"] },
  { id: "clima", label: "Clima", patterns: ["clima"] },
  { id: "nexo", label: "Nexo", patterns: ["nexo"] },
  { id: "campo", label: "Campo", patterns: ["campo"] },
  { id: "studio", label: "Studio", patterns: ["studio"] },
];

const qs = (selector) => document.querySelector(selector);
const create = (tag, className, text) => {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
};

let currentStatus = null;
let selectedStage = "pre-alpha";

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Data indisponível";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function setNotice(message, kind = "neutral") {
  const notice = qs("#notice");
  notice.textContent = message;
  notice.dataset.kind = kind;
  notice.hidden = !message;
}

function statusPill(status) {
  const pill = create("span", "status-pill", STATUS_LABELS[status] || status);
  pill.dataset.status = status;
  return pill;
}

function allChecks(status) {
  return status.stages.flatMap((stage) => stage.checks.map((check) => ({ ...check, stage: stage.id })));
}

function completion(checks) {
  if (!checks.length) return 0;
  const earned = checks.reduce((total, check) => total + (check.status === "PASS" ? 1 : check.status === "WARN" ? 0.65 : 0), 0);
  return Math.round((earned / checks.length) * 100);
}

function stageCompletion(stage) {
  if (!stage.checks.length) return stage.state === "approved" ? 100 : 0;
  return completion(stage.checks);
}

function nextStageId(status) {
  const current = status.stages.findIndex((stage) => stage.id === status.target_stage);
  if (status.result !== "PASS" || current < 0 || current >= status.stages.length - 1) return status.target_stage;
  return status.stages[current + 1].id;
}

function matches(check, patterns) {
  const haystack = `${check.id} ${check.description} ${check.detail || ""}`.toLowerCase();
  return patterns.some((pattern) => haystack.includes(pattern));
}

function renderHeader(status) {
  const warning = status.result === "PASS" && status.summary.warned > 0;
  const result = qs("#overall-result");
  result.dataset.status = warning ? "WARN" : status.result;
  result.querySelector("strong").textContent = warning
    ? "Aprovado com advertências"
    : STATUS_LABELS[status.result];
  qs("#heading-detail").textContent = `${STAGE_LABELS[status.target_stage]} · ${formatDate(status.generated_at)} · commit ${status.source.short_commit}`;
  qs("#target-stage").textContent = `Gate avaliado: ${STAGE_LABELS[status.target_stage]}`;
}

function renderExecutive(status) {
  const completed = status.result === "PASS" && status.summary.mandatory_failures === 0;
  const warning = status.summary.warned > 0;
  const currentLabel = STAGE_LABELS[status.target_stage];
  const nextLabel = STAGE_LABELS[nextStageId(status)];
  const confidence = completion(allChecks(status));
  qs("#executive-status").textContent = completed
    ? `${currentLabel} concluída${warning ? " com advertências" : ""}.`
    : `${currentLabel} ainda exige correção antes da promoção.`;
  qs("#next-stage").textContent = nextLabel;
  qs("#executive-blockers").textContent = status.summary.mandatory_failures;
  qs("#executive-warnings").textContent = status.summary.warned;
  qs("#confidence-score").textContent = `${confidence}%`;
  qs("#promotion-decision").textContent = completed ? "SIM" : "NÃO";
  qs("#promotion-detail").textContent = completed
    ? `Próxima avaliação sugerida: ${nextLabel}.`
    : "Resolver bloqueios obrigatórios antes de avançar.";
  qs(".decision-card").dataset.status = completed ? "PASS" : "FAIL";
}

function renderStages(stages) {
  const line = qs("#stage-line");
  line.replaceChildren();
  stages.forEach((stage, index) => {
    const item = create("li", "stage-step");
    item.dataset.state = stage.state;
    const marker = create("span", "stage-marker", stage.state === "approved" ? "✓" : stage.state === "blocked" ? "!" : String(index + 1));
    marker.setAttribute("aria-hidden", "true");
    const copy = create("span", "stage-copy");
    const meta = create("span", "stage-meta");
    meta.append(
      create("small", "", `${stageCompletion(stage)}%`),
      create("small", "", STAGE_STATE_LABELS[stage.state]),
      create("small", "", `${stage.checks.length} checks`),
    );
    const details = create("button", "stage-detail-button", "Detalhes");
    details.type = "button";
    details.addEventListener("click", () => {
      renderChecks(stage.id);
      qs("#checks-title").scrollIntoView({ block: "start", behavior: "smooth" });
    });
    copy.append(create("strong", "", stage.label), meta, details);
    item.append(marker, copy);
    line.append(item);
  });
}

function renderSummary(summary) {
  qs("#count-passed").textContent = summary.passed;
  qs("#count-failed").textContent = summary.failed;
  qs("#count-warned").textContent = summary.warned;
  qs("#count-skipped").textContent = summary.skipped;
  qs("#count-blockers").textContent = summary.mandatory_failures;
}

function renderBlockers(blockers) {
  const list = qs("#blockers-list");
  list.replaceChildren();
  if (!blockers.length) {
    const empty = create("p", "positive-empty", "Nenhum bloqueio obrigatório na última verificação.");
    list.append(empty);
    return;
  }
  blockers.forEach((blocker) => {
    const item = create("article", "blocker-item");
    const title = create("div", "blocker-title");
    title.append(statusPill("FAIL"), create("strong", "", blocker.id));
    item.append(title, create("p", "", blocker.description));
    if (blocker.detail) item.append(create("small", "", blocker.detail));
    list.append(item);
  });
}

function addDefinition(list, term, value, className = "") {
  const group = create("div", "provenance-item");
  group.append(create("dt", "", term), create("dd", className, value));
  list.append(group);
}

function renderProvenance(status) {
  const list = qs("#provenance-list");
  list.replaceChildren();
  
  if (status.evaluation) {
    const engineMap = { legacy: "Legado", declarative: "Declarativo", compare: "Compare (Paralelo)" };
    const modeMap = { check: "Verificação", certify: "Certificação" };
    addDefinition(list, "Motor", engineMap[status.evaluation.engine] || status.evaluation.engine);
    addDefinition(list, "Modo de Avaliação", modeMap[status.evaluation.mode] || status.evaluation.mode);
    if (status.evaluation.model_id) {
      addDefinition(list, "Modelo / Perfil", `${status.evaluation.model_id} / ${status.evaluation.profile_id}`, "mono");
    }
    if (status.evaluation.comparison?.performed) {
      addDefinition(list, "Equivalência", status.evaluation.comparison.equivalent ? "Comprovada" : "Divergente");
    }
  }

  addDefinition(list, "Commit", status.source.short_commit, "mono");
  addDefinition(list, "Branch", status.source.branch, "mono");
  addDefinition(list, "Árvore Git", status.source.dirty ? "Alterada" : "Limpa");
  addDefinition(list, "Verificador", status.verifier_version, "mono");
  addDefinition(list, "Schema", status.schema, "mono");
  addDefinition(list, "Atestação", status.attestation.available ? (status.attestation.signed ? "Assinada" : "Disponível") : "Não disponível");
}

function renderChecks(stageId) {
  selectedStage = stageId;
  const stage = currentStatus.stages.find((item) => item.id === stageId);
  document.querySelectorAll("[role=tab]").forEach((tab) => {
    const active = tab.dataset.stage === stageId;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  const body = qs("#checks-body");
  body.replaceChildren();
  qs("#check-count").textContent = `${stage.checks.length} checks`;
  qs("#checks-empty").hidden = stage.checks.length !== 0;
  stage.checks.forEach((check) => {
    const row = create("tr");
    const statusCell = create("td");
    statusCell.append(statusPill(check.status));
    const idCell = create("td", "mono", check.id);
    const descriptionCell = create("td", "", check.description);
    const requiredCell = create("td", "", check.mandatory ? "Sim" : "Não");
    const evidenceCell = create("td", "evidence-cell");
    if (check.evidence.length) {
      check.evidence.forEach((path) => evidenceCell.append(create("code", "", path)));
    } else {
      evidenceCell.textContent = "—";
    }
    const detailCell = create("td", "detail-cell", check.detail || "—");
    row.append(statusCell, idCell, descriptionCell, requiredCell, evidenceCell, detailCell);
    body.append(row);
  });
}

function renderStageTabs(stages) {
  const tabs = qs("#stage-tabs");
  tabs.replaceChildren();
  stages.forEach((stage) => {
    const button = create("button", "stage-tab", stage.label);
    button.type = "button";
    button.role = "tab";
    button.dataset.stage = stage.id;
    button.setAttribute("aria-selected", "false");
    button.addEventListener("click", () => renderChecks(stage.id));
    button.addEventListener("keydown", (event) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      const index = stages.findIndex((item) => item.id === selectedStage);
      const offset = event.key === "ArrowRight" ? 1 : -1;
      const next = stages[(index + offset + stages.length) % stages.length].id;
      renderChecks(next);
      tabs.querySelector(`[data-stage="${next}"]`).focus();
    });
    tabs.append(button);
  });
  renderChecks(currentStatus.target_stage);
}

function renderActions(actions) {
  const list = qs("#actions-list");
  list.replaceChildren();
  actions.forEach((action) => list.append(create("li", "", action)));
}

function renderOperationalAction(status) {
  const command = "./scripts/maturity/run-and-publish.sh";
  qs("#publish-command").textContent = command;
  qs("#copy-publish-command").dataset.command = command;
  qs("#copy-publish-command").textContent = "Copiar";
  qs("#operation-detail").textContent = `Sem argumento, o script infere o estágio atual e hoje deve publicar ${STAGE_LABELS[status.target_stage]}.`;
}

function renderHistory(history) {
  const body = qs("#history-body");
  body.replaceChildren();
  const items = history?.items?.slice(0, 10) || [];
  qs("#history-empty").hidden = items.length !== 0;
  items.forEach((item) => {
    const row = create("tr");
    row.append(
      create("td", "", formatDate(item.generated_at)),
      create("td", "", STAGE_LABELS[item.target_stage]),
      (() => { const cell = create("td"); cell.append(statusPill(item.result)); return cell; })(),
      create("td", "mono", item.short_commit),
    );
    body.append(row);
  });
}

function renderEngineeringHealth(status) {
  const checks = allChecks(status);
  const list = qs("#engineering-health");
  list.replaceChildren();
  ENGINEERING_DIMENSIONS.forEach((dimension) => {
    const matched = checks.filter((check) => matches(check, dimension.patterns));
    const score = completion(matched);
    const row = create("div", "health-row");
    const label = create("span", "", dimension.label);
    const meter = create("span", "health-meter");
    const fill = create("span");
    fill.style.width = `${score}%`;
    meter.append(fill);
    row.append(label, meter, create("strong", "", `${score}%`));
    list.append(row);
  });
}

function renderSubsystems(status) {
  const checks = allChecks(status);
  const list = qs("#subsystems-list");
  list.replaceChildren();
  const platform = create("article", "subsystem-item subsystem-platform");
  platform.append(create("strong", "", "SisTer"), statusPill(status.result), create("span", "", STAGE_LABELS[status.target_stage]));
  list.append(platform);
  SUBSYSTEMS.forEach((subsystem) => {
    const matched = checks.filter((check) => matches(check, subsystem.patterns));
    const result = !matched.length ? "SKIP" : matched.some((check) => check.status === "FAIL" && check.mandatory) ? "FAIL" : matched.some((check) => check.status === "WARN" || check.status === "FAIL") ? "WARN" : "PASS";
    const item = create("article", "subsystem-item");
    item.append(create("strong", "", subsystem.label), statusPill(result), create("span", "", matched.length ? `${completion(matched)}%` : "Sem evidência"));
    list.append(item);
  });
}

function renderDecisionTree(status) {
  const stage = status.stages.find((item) => item.id === status.target_stage);
  const tree = qs("#decision-tree");
  tree.replaceChildren();
  stage.checks.forEach((check) => {
    const row = create("div", "decision-node");
    row.append(statusPill(check.status), create("strong", "mono", check.id), create("span", "", check.description));
    tree.append(row);
  });
  const answer = create("div", "decision-answer");
  const promoted = status.result === "PASS" && status.summary.mandatory_failures === 0;
  answer.dataset.status = promoted ? "PASS" : "FAIL";
  answer.append(create("span", "", "Pode promover?"), create("strong", "", promoted ? "SIM" : "NÃO"));
  tree.append(answer);
}

function renderDashboard(status, history) {
  currentStatus = status;
  renderHeader(status);
  renderExecutive(status);
  renderStages(status.stages);
  renderSummary(status.summary);
  renderBlockers(status.blockers);
  renderProvenance(status);
  renderEngineeringHealth(status);
  renderSubsystems(status);
  renderDecisionTree(status);
  renderStageTabs(status.stages);
  renderActions(status.next_actions);
  renderOperationalAction(status);
  renderHistory(history);
  qs("#dashboard").hidden = false;
  setNotice("");
}

async function fetchJson(path, optional = false) {
  const response = await fetch(path, { cache: "no-store", headers: { Accept: "application/json" } });
  if (optional && response.status === 404) return null;
  if (response.status === 401) {
    window.location.assign("/login");
    throw new Error("unauthorized");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Falha HTTP ${response.status}`);
  }
  return response.json();
}

async function loadDashboard() {
  const button = qs("#refresh-button");
  button.disabled = true;
  setNotice("Consultando evidência...", "neutral");
  try {
    const [user, status, history] = await Promise.all([
      fetchJson("/api/me"),
      fetchJson("/api/admin/maturity/latest"),
      fetchJson("/api/admin/maturity/history", true),
    ]);
    qs("#admin-name").textContent = user.name;
    renderDashboard(status, history);
  } catch (error) {
    qs("#dashboard").hidden = true;
    if (error.message !== "unauthorized") {
      setNotice(error.message || "Não foi possível carregar a evidência de maturidade.", "error");
      qs("#overall-result").dataset.status = "FAIL";
      qs("#overall-result strong").textContent = "Indisponível";
      qs("#heading-detail").textContent = "Nenhuma evidência válida pôde ser apresentada.";
    }
  } finally {
    button.disabled = false;
  }
}

qs("#refresh-button").addEventListener("click", loadDashboard);
qs("#copy-publish-command").addEventListener("click", async () => {
  const button = qs("#copy-publish-command");
  const command = button.dataset.command || qs("#publish-command").textContent;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(command);
    } else {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(qs("#publish-command"));
      selection.removeAllRanges();
      selection.addRange(range);
      document.execCommand("copy");
      selection.removeAllRanges();
    }
    button.textContent = "Copiado";
  } catch (_) {
    button.textContent = "Selecionar";
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(qs("#publish-command"));
    selection.removeAllRanges();
    selection.addRange(range);
  }
});
loadDashboard();
