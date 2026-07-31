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

function renderStages(stages) {
  const line = qs("#stage-line");
  line.replaceChildren();
  stages.forEach((stage, index) => {
    const item = create("li", "stage-step");
    item.dataset.state = stage.state;
    const marker = create("span", "stage-marker", stage.state === "approved" ? "✓" : stage.state === "blocked" ? "!" : String(index + 1));
    marker.setAttribute("aria-hidden", "true");
    const copy = create("span", "stage-copy");
    copy.append(create("strong", "", stage.label), create("small", "", STAGE_STATE_LABELS[stage.state]));
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

function renderDashboard(status, history) {
  currentStatus = status;
  renderHeader(status);
  renderStages(status.stages);
  renderSummary(status.summary);
  renderBlockers(status.blockers);
  renderProvenance(status);
  renderStageTabs(status.stages);
  renderActions(status.next_actions);
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
loadDashboard();
