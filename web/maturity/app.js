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

// Componentes agregados vindo do backend
const GOVERNANCE_LABELS = {
  governed: "Governado",
  shadow: "Shadow",
  none: "Não iniciado"
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

function activatePanel(panelId) {
  document.querySelectorAll("[data-panel-tab]").forEach((tab) => {
    tab.setAttribute("aria-selected", String(tab.dataset.panelTab === panelId));
  });
  document.querySelectorAll("[data-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.panel !== panelId;
  });
}

function evaluatedComponent(status) {
  return status.evaluation?.profile_id || status.evaluation?.component || "sister-core";
}

function componentLabel(id) {
  const labels = {
    "sister-core": "SisTer Core",
    "sister-clima": "Sister-Clima",
    "sister-nexo": "SisTer Nexo",
  };
  return labels[id] || id;
}

function engineLabel(engine) {
  const engineMap = { legacy: "Legado", declarative: "Declarativo", compare: "Compare" };
  return engineMap[engine] || engine || "Não informado";
}

function governanceLabel(status) {
  const mode = status.evaluation?.evaluation_mode;
  if (mode === "shadow" || status.promotion?.applicable === false) return "Shadow";
  if (mode === "governed" || status.promotion?.applicable === true) return "Governed";
  return "Não declarado";
}

function scopeLayer(status) {
  if (status.evaluation?.engine === "compare") return "Componente + SGE/engine + governança";
  return "Componente + governança";
}

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
  qs("#heading-detail").textContent = `${componentLabel(evaluatedComponent(status))} · gate ${STAGE_LABELS[status.target_stage]} · ${formatDate(status.generated_at)} · commit ${status.source.short_commit}`;
  qs("#target-stage").textContent = `Gate avaliado: ${STAGE_LABELS[status.target_stage]}`;
}

function renderExecutive(status) {
  const completed = status.result === "PASS" && status.summary.mandatory_failures === 0;
  const warning = status.summary.warned > 0;
  const currentLabel = STAGE_LABELS[status.target_stage];
  const nextLabel = STAGE_LABELS[nextStageId(status)];
  const confidence = completion(allChecks(status));
  
  let decisionText = completed ? "SIM" : "NÃO";
  let detailText = completed
    ? `O componente pode avançar para a próxima avaliação sugerida: ${nextLabel}.`
    : "Resolver bloqueios obrigatórios do componente antes de avançar.";
  let cardStatus = completed ? "PASS" : "FAIL";

  if (status.promotion && !status.promotion.applicable) {
    decisionText = "SHADOW";
    detailText = "Avaliação técnica registrada em modo shadow. Promoção não aplicável ao ecossistema.";
    cardStatus = "SHADOW";
  }

  qs("#executive-status").textContent = completed
    ? `${componentLabel(evaluatedComponent(status))}: gate ${currentLabel} aprovado${warning ? " com advertências" : ""}.`
    : `${componentLabel(evaluatedComponent(status))}: gate ${currentLabel} ainda exige correção.`;
  qs("#evaluated-target").textContent = componentLabel(evaluatedComponent(status));
  qs("#evaluation-scope").textContent = scopeLayer(status);
  qs("#next-stage").textContent = nextLabel;
  qs("#executive-blockers").textContent = status.summary.mandatory_failures;
  qs("#executive-warnings").textContent = status.summary.warned;
  qs("#confidence-score").textContent = `${confidence}%`;
  qs("#promotion-decision").textContent = decisionText;
  qs("#promotion-detail").textContent = detailText;
  qs(".decision-card").dataset.status = cardStatus;
}

function renderScope(status) {
  const comparison = status.evaluation?.comparison;
  const impact = status.promotion?.applicable === false
    ? "Não bloqueia promoção global"
    : status.promotion?.recommendation === "promote"
      ? "Pode recomendar avanço do componente"
      : "Bloqueia avanço do componente";
  qs("#scope-layer").textContent = scopeLayer(status);
  qs("#scope-component").textContent = componentLabel(evaluatedComponent(status));
  qs("#scope-stage").textContent = STAGE_LABELS[status.target_stage] || status.target_stage;
  qs("#scope-engine").textContent = comparison?.performed
    ? `${engineLabel(status.evaluation.engine)} · ${comparison.status || (comparison.equivalent ? "EQUIVALENT" : "DIVERGENT")}`
    : engineLabel(status.evaluation?.engine);
  qs("#scope-governance").textContent = governanceLabel(status);
  qs("#scope-impact").textContent = impact;
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
      activatePanel("evidence");
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
    const modeMap = { check: "Verificação", certify: "Certificação" };
    addDefinition(list, "Engine SGE", engineLabel(status.evaluation.engine));
    addDefinition(list, "Modo de Avaliação", modeMap[status.evaluation.mode] || status.evaluation.mode);
    addDefinition(list, "Componente avaliado", componentLabel(evaluatedComponent(status)));
    addDefinition(list, "Governança", governanceLabel(status));
    if (status.evaluation.model_id) {
      addDefinition(list, "Modelo / Perfil", `${status.evaluation.model_id} / ${status.evaluation.profile_id}`, "mono");
    }
    if (status.evaluation.comparison?.performed) {
      addDefinition(list, "Compare", status.evaluation.comparison.equivalent ? "Equivalente" : "Divergente");
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
  const command = "./scripts/sge maturity publish-all";
  qs("#publish-command").textContent = command;
  qs("#copy-publish-command").dataset.command = command;
  qs("#copy-publish-command").textContent = "Copiar";
  qs("#operation-detail").textContent = `Executa todos os componentes resolvíveis. Use publish ${status.target_stage} para diagnóstico focal do componente atual.`;
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

function renderComponents(index) {
  const list = qs("#subsystems-list");
  list.replaceChildren();

  const components = index?.components || [];
  if (!components.length) {
    list.append(create("p", "positive-empty", "Nenhum componente federado disponível."));
    return;
  }

  components.forEach((comp) => {
    const item = create("article", "subsystem-item");
    const title = create("strong", "", comp.label);
    
    // Status text (Governado, Shadow, Sem perfil)
    let govText = GOVERNANCE_LABELS[comp.governance_mode] || "Sem perfil";
    if (comp.profile_state === "missing") govText = "Sem perfil";

    const resultText = comp.technical_result ? `${STAGE_LABELS[comp.stage] || comp.stage} — ${comp.technical_result}` : "Não avaliado";
    const technicalPill = statusPill(comp.technical_result || "SKIP");
    technicalPill.textContent = resultText;

    let govType = "SKIP";
    if (comp.governance_mode === "shadow") govType = "SHADOW";
    else if (comp.governance_mode === "governed") govType = "PASS";
    
    const govPill = statusPill(govType);
    govPill.textContent = govText.toUpperCase();

    item.append(title, technicalPill, govPill);
    list.append(item);
  });
}

function renderCatalog(catalog) {
  const grid = qs("#checks-catalog");
  grid.replaceChildren();
  if (catalog?.unavailable) {
    const message = create("div", "unavailable-state");
    message.append(
      create("strong", "", "Catálogo indisponível"),
      create("p", "", catalog.detail || "O servidor não disponibilizou o catálogo de testes."),
      create("code", "mono", "./scripts/sge maturity components"),
    );
    grid.append(message);
    return;
  }
  const components = catalog?.components || [];
  if (!components.length) {
    grid.append(create("p", "positive-empty", "Catálogo de checks ainda não publicado."));
    return;
  }
  components.forEach((component) => {
    const card = create("article", "catalog-card");
    const header = create("div", "catalog-card-header");
    header.append(
      create("strong", "", componentLabel(component.component_id)),
      create("span", "", `${component.total_checks || 0} checks`),
    );
    const stages = create("dl", "catalog-stage-list");
    Object.entries(component.checks_by_stage || {}).forEach(([stage, count]) => {
      const group = create("div");
      group.append(create("dt", "", STAGE_LABELS[stage] || stage), create("dd", "", String(count)));
      stages.append(group);
    });
    const checks = create("div", "catalog-check-list");
    (component.checks || []).slice(0, 8).forEach((check) => {
      const row = create("div", "catalog-check");
      row.append(create("span", "mono", check.id), create("small", "", `${STAGE_LABELS[check.stage] || check.stage} · ${check.type}${check.mandatory ? " · obrigatório" : ""}`));
      checks.append(row);
    });
    if ((component.checks || []).length > 8) {
      checks.append(create("small", "catalog-more", `+${component.checks.length - 8} checks no perfil`));
    }
    card.append(header, stages, checks);
    grid.append(card);
  });
}

function formatDuration(milliseconds) {
  if (!Number.isFinite(milliseconds)) return "—";
  if (milliseconds < 1000) return `${milliseconds} ms`;
  return `${(milliseconds / 1000).toFixed(milliseconds < 10000 ? 1 : 0)} s`;
}

function renderQuality(quality) {
  const body = qs("#quality-body");
  body.replaceChildren();
  const empty = qs("#quality-empty");
  const result = qs("#quality-result");
  if (!quality || quality.unavailable) {
    empty.hidden = false;
    result.dataset.status = "SKIP";
    result.querySelector("strong").textContent = "Não publicada";
    qs("#quality-meta").textContent = quality?.detail || "Execute ./scripts/run_quality.sh para publicar os resultados.";
    ["total", "passed", "failed", "skipped"].forEach((key) => { qs(`#quality-${key}`).textContent = "0"; });
    return;
  }

  empty.hidden = true;
  result.dataset.status = quality.result;
  result.querySelector("strong").textContent = STATUS_LABELS[quality.result] || quality.result;
  qs("#quality-meta").textContent = `${formatDate(quality.finished_at)} · commit ${quality.source?.short_commit || "não informado"} · árvore ${quality.source?.worktree === "clean" ? "limpa" : "com alterações"}`;
  ["total", "passed", "failed", "skipped"].forEach((key) => {
    qs(`#quality-${key}`).textContent = String(quality.summary?.[key] || 0);
  });
  (quality.steps || []).forEach((step) => {
    const commandCell = create("td");
    commandCell.append(create("code", "mono", (step.command || []).join(" ")));
    const stateCell = create("td");
    stateCell.append(statusPill(step.status));
    const exit = step.exit_code === null || step.exit_code === undefined ? "—" : `exit ${step.exit_code}`;
    const row = create("tr");
    row.append(stateCell, create("td", "", step.label), commandCell, create("td", "mono", formatDuration(step.duration_ms)), create("td", "mono", exit));
    body.append(row);
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
  if (status.promotion && !status.promotion.applicable) {
    answer.dataset.status = "SHADOW";
    answer.append(create("span", "", "Promoção do componente"), create("strong", "", "SHADOW"));
  } else {
    answer.dataset.status = promoted ? "PASS" : "FAIL";
    answer.append(create("span", "", "Promoção do componente"), create("strong", "", promoted ? "SIM" : "NÃO"));
  }
  tree.append(answer);
}

function renderDashboard(status, history, components, catalog, quality) {
  currentStatus = status;
  renderHeader(status);
  renderExecutive(status);
  renderScope(status);
  renderStages(status.stages);
  renderCatalog(catalog);
  renderQuality(quality);
  renderSummary(status.summary);
  renderBlockers(status.blockers);
  renderProvenance(status);
  renderEngineeringHealth(status);
  renderComponents(components);
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

async function fetchPublishedJson(path) {
  const response = await fetch(path, { cache: "no-store", headers: { Accept: "application/json" } });
  if (response.status === 401) {
    window.location.assign("/login");
    throw new Error("unauthorized");
  }
  const payload = await response.json().catch(() => ({}));
  if (response.status === 404) {
    return { unavailable: true, detail: payload?.error?.detail || payload?.detail || "Recurso ainda não publicado ou servidor desatualizado." };
  }
  if (!response.ok) throw new Error(payload?.error?.detail || payload?.detail || `Falha HTTP ${response.status}`);
  return payload;
}

async function loadDashboard() {
  const button = qs("#refresh-button");
  button.disabled = true;
  setNotice("Consultando evidência...", "neutral");
  try {
    const [user, status, history, components, catalog, quality] = await Promise.all([
      fetchJson("/api/me"),
      fetchJson("/api/admin/maturity/latest"),
      fetchJson("/api/admin/maturity/history", true),
      fetchJson("/api/admin/maturity/components", true),
      fetchPublishedJson("/api/admin/maturity/catalog"),
      fetchPublishedJson("/api/admin/maturity/quality"),
    ]);
    qs("#admin-name").textContent = user.name;
    renderDashboard(status, history, components, catalog, quality);
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
qs("#core-scope-toggle").addEventListener("click", () => {
  const detail = qs("#core-scope-detail");
  detail.hidden = !detail.hidden;
  qs("#core-scope-toggle").textContent = detail.hidden
    ? "O que significa testar SisTer Core?"
    : "Ocultar explicação sobre SisTer Core";
});
document.querySelectorAll("[data-panel-tab]").forEach((tab) => {
  tab.addEventListener("click", () => activatePanel(tab.dataset.panelTab));
});
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
