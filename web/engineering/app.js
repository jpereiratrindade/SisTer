const emptyOperationalBase = {
  unavailable: true,
  unavailable_reason: "not_loaded",
  offers: [],
  requirements: [],
  candidates: [],
  capabilities: [],
  purpose: {
    id: "PurposeDefinition",
    title: "Propósito operacional não publicado",
    status: "MISSING",
    detail: "Definir qual propósito rege uma operação hipotética mínima."
  },
  functions: [],
  process: {
    id: "OperationalProcessDefinition",
    title: "Processo aprovado não publicado",
    status: "MISSING",
    detail: "Definir ordem, pré-condições, entradas, saídas e evidências obrigatórias."
  },
  approval: {
    status: "MISSING",
    authority: "engenheiro responsável",
    detail: "A estrutura operacional ainda não foi aprovada."
  },
  instance: {
    id: "ProcessInstance",
    status: "NOT_CREATED",
    detail: "Nenhuma instância concreta foi criada a partir de processo aprovado."
  },
  execution: {
    status: "NOT_RECORDED",
    expected: "FunctionExecution com evidência persistida.",
    observed: "Sem execução registrada."
  },
  observation: {
    status: "NOT_RECORDED",
    evidence: []
  },
  assessment: {
    status: "NOT_AVAILABLE",
    comparison: "Sem esperado × observado persistido.",
    recommendation: "Implementar a base operacional mínima antes de integrar subsistemas reais.",
    human_decision: "aprovar estrutura operacional"
  }
};

const operationSteps = [
  { id: "requirement", label: "Necessidade", contract: "CapabilityRequirement" },
  { id: "capability", label: "Capacidade", contract: "CapabilityOffer" },
  { id: "contract", label: "Contrato", contract: "IntegrationDefinition" },
  { id: "execution", label: "Execução", contract: "IntegrationExecution" },
  { id: "observation", label: "Observação", contract: "OperationalObservation" },
  { id: "assessment", label: "Avaliação", contract: "OperationalAssessment" },
  { id: "recommendation", label: "Recomendação", contract: "Recommendation" },
  { id: "decision", label: "Nova decisão", contract: "EngineeringDecision" }
];

const $ = selector => document.querySelector(selector);
const esc = value => {
  const div = document.createElement("div");
  div.textContent = value || "";
  return div.innerHTML;
};

function healthLabel(status) {
  if (status === "online") return "online";
  if (status === "offline") return "offline";
  return "não observado";
}

function renderEcosystem(ecosystem) {
  const systems = Array.isArray(ecosystem?.systems) ? ecosystem.systems : [];
  const online = systems.filter(system => system.health?.status === "online").length;
  const published = systems.filter(system => Boolean(system.gateway?.public_url)).length;
  $("#ecosystem-summary").innerHTML = `
    <article><span>Composição</span><strong>${esc(ecosystem?.composition_id || "não configurada")}</strong></article>
    <article><span>Deployment</span><strong>${esc(ecosystem?.deployment_status || "não configurado")}</strong></article>
    <article><span>Health</span><strong>${online}/${systems.length} online</strong></article>
    <article><span>Publicação</span><strong>${published}/${systems.length} publicados</strong></article>`;

  $("#ecosystem-grid").innerHTML = systems.length ? systems.map(system => `
    <article class="ecosystem-card">
      <div><span class="eyebrow">${esc(system.component_id)}</span><h3>${esc(system.system_id)}</h3></div>
      <dl>
        <div><dt>Runtime</dt><dd>${esc(system.runtime?.transport || "-")} · ${esc(system.runtime?.listen || "-")}:${esc(system.runtime?.port || "-")}</dd></div>
        <div><dt>Probe</dt><dd>${esc(system.probe?.health_path || "não declarado")}</dd></div>
        <div><dt>Health</dt><dd>${esc(healthLabel(system.health?.status))} · ${esc(system.health?.detail || "-")}</dd></div>
        <div><dt>Gateway</dt><dd>${esc(system.gateway?.public_url || system.gateway?.host || "não publicado")}</dd></div>
      </dl>
    </article>`).join("") : `<p class="ecosystem-empty">Nenhum componente declarado na projeção operacional.</p>`;
}

async function loadEcosystem() {
  const button = $("#refresh-ecosystem");
  if (button) button.disabled = true;
  try {
    const response = await fetch("/api/ecosystem", {cache: "no-store"});
    renderEcosystem(response.ok ? await response.json() : null);
  } catch {
    renderEcosystem(null);
  } finally {
    if (button) button.disabled = false;
  }
}

function statusLabel(status) {
  return {
    APPROVED: "aprovado",
    ACTIVE: "ativo",
    COMPLETED: "concluído",
    INCONCLUSIVE: "inconclusivo",
    MISSING: "ausente",
    NOT_CREATED: "não criada",
    NOT_RECORDED: "não registrada",
    NOT_AVAILABLE: "indisponível",
    PENDING_APPROVAL: "aguarda aprovação",
    AWAITING_SIGNATURE_AND_APPROVAL: "aguarda assinatura e aprovação"
  }[status] || String(status || "indefinido").toLowerCase();
}

function stepStatus(base, step) {
  if (step.id === "requirement") return (base.requirements || []).length ? "ACTIVE" : "MISSING";
  if (step.id === "capability") return (base.offers || []).length ? "ACTIVE" : "MISSING";
  if (step.id === "contract") return (base.candidates || []).length || (base.capabilities || []).length ? base.approval?.status || "PENDING_APPROVAL" : "MISSING";
  if (step.id === "recommendation") return base.assessment?.recommendation ? base.assessment.status : "NOT_AVAILABLE";
  if (step.id === "decision") return base.assessment?.human_decision ? "PENDING_APPROVAL" : "MISSING";
  return base[step.id]?.status || "MISSING";
}

function stepDetail(base, step) {
  if (step.id === "requirement") {
    const requirements = base.requirements || [];
    if (!requirements.length) return "Nenhuma necessidade concreta registrada.";
    return requirements.map(req => `${req.subsystem_id}: ${req.needed_capability}`).join(" · ");
  }
  if (step.id === "capability") {
    const offers = base.offers || [];
    if (!offers.length) return "Nenhuma oferta concreta registrada.";
    return offers.map(offer => `${offer.subsystem_id}: ${offer.capability}`).join(" · ");
  }
  if (step.id === "contract") {
    const candidates = base.candidates || [];
    if (capabilitiesFor(base).length) return "Contrato aprovado, assinado e verificado.";
    if (!candidates.length) return "Nenhuma definição de integração registrada.";
    return candidates.map(candidate => `${candidate.id}: ${statusLabel(candidate.status)}`).join(" · ");
  }
  if (step.id === "recommendation") return base.assessment?.recommendation || "Sem recomendação persistida.";
  if (step.id === "decision") return base.assessment?.human_decision || "Sem decisão de engenharia pendente.";
  if (step.id === "execution") return base.execution?.observed || base.execution?.expected || "Sem execução registrada.";
  if (step.id === "observation") {
    const evidence = base.observation?.evidence || [];
    return evidence.length ? evidence.join(" · ") : "Sem evidência observada.";
  }
  return base[step.id]?.detail || base[step.id]?.title || "Objeto operacional não publicado.";
}

function capabilityStatusLabel(status) {
  return {
    APROVADA: "aprovada",
    EM_CONSTRUCAO: "em construção",
    PLANEJADA: "planejada",
    OBSERVADA: "observada"
  }[status] || statusLabel(status);
}

function capabilitiesFor(base) {
  if (!base.capability_source?.signed_contracts_verified) return [];
  return base.capabilities || [];
}

function renderCapabilities(base) {
  const capabilities = capabilitiesFor(base);
  const offers = base.offers || [];
  const requirements = base.requirements || [];
  const candidates = base.candidates || [];
  $("#capability-count").textContent = `${capabilities.length} capacidades`;
  if (!capabilities.length) {
    const unavailableMessage = base.unavailable_reason === "authentication_required"
      ? "Autenticação necessária para ler a Base Operacional no PostgreSQL."
      : "A capacidade só será promovida quando oferta, requisito e definição de integração forem contratos concretos assinados, aprovados e verificados.";
    $("#capability-grid").innerHTML = `<article class="capability-empty">
      <h3>${base.unavailable_reason === "authentication_required" ? "Base operacional protegida" : (candidates.length ? "Integração candidata detectada" : "Nenhuma capacidade operacional aprovada registrada")}</h3>
      <p>${esc(candidates[0]?.title || "O sistema simulado/de referência pode entregar ofertas de capacidade, mas isso ainda não é capacidade adquirida pelo SisTer.")}</p>
      <p>${esc(candidates[0]?.recommendation || unavailableMessage)}</p>
      <dl class="source-counts">
        <div><dt>Ofertas publicadas</dt><dd>${offers.length}</dd></div>
        <div><dt>Necessidades publicadas</dt><dd>${requirements.length}</dd></div>
        <div><dt>Integrações candidatas</dt><dd>${candidates.length}</dd></div>
      </dl>
      ${renderContractAnalysis(offers, requirements, candidates)}
      <small>${esc(candidates[0]?.status ? statusLabel(candidates[0].status) : "Fonte autoritativa: PostgreSQL do sisterd")}</small>
    </article>`;
    return;
  }
  $("#capability-grid").innerHTML = capabilities.map(capability => `
    <article class="capability-card" data-capability="${esc(capability.id)}">
      <div class="capability-status">${esc(capabilityStatusLabel(capability.status))}</div>
      <h3>${esc(capability.title)}</h3>
      <p>${esc(capability.purpose)}</p>
      <dl>
        <div><dt>Processo</dt><dd>${esc(capability.process)}</dd></div>
        <div><dt>Funções</dt><dd>${esc((capability.functions || []).join(" · "))}</dd></div>
      </dl>
    </article>
  `).join("");
  $("#capability-grid").querySelectorAll("[data-capability]").forEach(card => {
    card.addEventListener("click", () => showCapability(capabilities.find(capability => capability.id === card.dataset.capability)));
  });
}

function renderContractAnalysis(offers, requirements, candidates) {
  if (!offers.length && !requirements.length && !candidates.length) {
    return `<div class="contract-analysis"><strong>Análise do SisTer</strong><p>Sem contratos registrados no PostgreSQL para analisar.</p></div>`;
  }
  return `<div class="contract-analysis">
    <strong>Análise do SisTer sobre os contratos registrados</strong>
    <div class="contract-analysis-grid">
      <section>
        <h4>Ofertas</h4>
        ${offers.length ? offers.map(offer => `<p><b>${esc(offer.subsystem_id)}</b> oferece <b>${esc(offer.capability)}</b><br><small>${esc((offer.produces || []).join(" · ")) || "sem dados produzidos declarados"} · ${esc(offer.contract_schema || "schema não declarado")} ${esc(offer.contract_version || "")}</small></p>`).join("") : "<p>Nenhuma oferta publicada.</p>"}
      </section>
      <section>
        <h4>Necessidades</h4>
        ${requirements.length ? requirements.map(requirement => `<p><b>${esc(requirement.subsystem_id)}</b> necessita <b>${esc(requirement.needed_capability)}</b><br><small>${esc(requirement.expected_schema || "schema esperado não declarado")} ${esc(requirement.expected_version || "")}</small></p>`).join("") : "<p>Nenhuma necessidade publicada.</p>"}
      </section>
      <section>
        <h4>Candidatas</h4>
        ${candidates.length ? candidates.map(candidate => `<p><b>${esc(candidate.title)}</b><br><small>${esc(candidate.objective || candidate.recommendation || "sem objetivo declarado")}</small></p>`).join("") : "<p>Nenhuma candidata detectada.</p>"}
      </section>
    </div>
  </div>`;
}

function renderContracts(base) {
  const offers = base.offers || [];
  const requirements = base.requirements || [];
  const candidates = base.candidates || [];
  $("#contracts-state").textContent = `${offers.length} ofertas · ${requirements.length} necessidades · ${candidates.length} candidatas`;
  $("#contracts-grid").innerHTML = `
    <article>
      <h3>Necessidades</h3>
      ${requirements.length ? requirements.map(requirement => `
        <section class="contract-row">
          <strong>${esc(requirement.needed_capability)}</strong>
          <p>${esc(requirement.purpose || "Sem finalidade declarada.")}</p>
          <small>${esc(requirement.subsystem_id)} · ${esc(requirement.expected_schema || "schema esperado ausente")} · ${esc(statusLabel(requirement.status))}</small>
        </section>
      `).join("") : "<p>Nenhuma necessidade registrada.</p>"}
    </article>
    <article>
      <h3>Capacidades ofertadas</h3>
      ${offers.length ? offers.map(offer => `
        <section class="contract-row">
          <strong>${esc(offer.capability)}</strong>
          <p>${esc((offer.produces || []).join(" · ") || "Sem dado produzido declarado.")}</p>
          <small>${esc(offer.subsystem_id)} · ${esc(offer.contract_schema || "schema ausente")} · ${esc(statusLabel(offer.status))}</small>
        </section>
      `).join("") : "<p>Nenhuma oferta registrada.</p>"}
    </article>
    <article>
      <h3>Integrações candidatas</h3>
      ${candidates.length ? candidates.map(candidate => `
        <section class="contract-row">
          <strong>${esc(candidate.title || candidate.id)}</strong>
          <p>${esc(candidate.objective || candidate.recommendation || "Sem objetivo declarado.")}</p>
          <small>${esc(candidate.id)} · ${esc(statusLabel(candidate.status))}</small>
          <div class="contract-actions">
            <button type="button" data-integration-decision="approved" data-integration-id="${esc(candidate.id)}" data-integration-version="${esc(candidate.version || "1.0.0")}">Aprovar</button>
            <button type="button" data-integration-decision="rejected" data-integration-id="${esc(candidate.id)}" data-integration-version="${esc(candidate.version || "1.0.0")}">Rejeitar</button>
          </div>
        </section>
      `).join("") : "<p>Nenhuma candidata detectada.</p>"}
    </article>
  `;
  $("#contracts-grid").querySelectorAll("[data-integration-decision]").forEach(button => {
    button.addEventListener("click", () => decideIntegration(button));
  });
}

async function decideIntegration(button) {
  const integrationId = button.dataset.integrationId;
  const version = button.dataset.integrationVersion;
  const decision = button.dataset.integrationDecision;
  const rationale = prompt(
    decision === "approved"
      ? "Justificativa para aprovar esta integração:"
      : "Justificativa para rejeitar esta integração:",
    decision === "approved"
      ? "Contratos revisados pela engenharia; integração apta a entrar na Base Operacional."
      : "Contratos insuficientes para promover capacidade operacional."
  );
  if (!rationale || !rationale.trim()) return;
  button.disabled = true;
  const response = await fetch(
    `/api/v1/engineering/integrations/${encodeURIComponent(integrationId)}/${encodeURIComponent(version)}/decision`,
    {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({decision, rationale: rationale.trim()})
    }
  );
  if (!response.ok) {
    button.disabled = false;
    alert("Decisão não aplicada pela Base Operacional.");
    return;
  }
  const base = await fetchJsonOrFallback(
    "/api/v1/engineering/operational-base/current",
    emptyOperationalBase
  );
  render(base);
}

function renderOperation(base) {
  $("#operation-map").innerHTML = operationSteps.map((step, index) => {
    const status = stepStatus(base, step);
    return `<article class="operation-card ${status === "MISSING" || status.startsWith("NOT_") ? "missing" : "ready"}">
      <span class="operation-index">${index + 1}</span>
      <div>
        <strong>${esc(step.label)}</strong>
        <small>${esc(step.contract)} · ${esc(statusLabel(status))}</small>
        <p>${esc(stepDetail(base, step))}</p>
      </div>
    </article>`;
  }).join("");
}

function renderAssessment(base) {
  $("#assessment-status").textContent = statusLabel(base.assessment?.status);
  $("#assessment-grid").innerHTML = `
    <article><span>Esperado</span><p>${esc(base.execution?.expected || "Execução esperada ainda não definida.")}</p></article>
    <article><span>Observado</span><p>${esc(base.execution?.observed || "Nenhuma execução observada.")}</p></article>
    <article><span>Comparação</span><p>${esc(base.assessment?.comparison || "Sem comparação persistida.")}</p></article>
    <article><span>Recomendação</span><p>${esc(base.assessment?.recommendation || "Sem recomendação persistida.")}</p></article>
  `;
}

function render(operationalBase) {
  const base = operationalBase || emptyOperationalBase;

  $("#objective").textContent = base.unavailable
    ? (base.unavailable_reason === "authentication_required"
      ? "Base operacional protegida · autenticação necessária"
      : "Base operacional ainda não publicada · nenhuma capacidade pode ser inferida do frontend")
    : `${base.purpose?.title || "Propósito operacional"} · ${base.process?.title || "processo aprovado"}`;
  $("#revision").textContent = base.schema || "sister.operational-base";
  $("#capabilities-summary").textContent = `${capabilitiesFor(base).length} aprovadas · ${(base.offers || []).length} ofertas`;
  $("#purpose-title").textContent = base.purpose?.title || "não publicado";
  $("#process-title").textContent = base.process?.title || "não publicado";
  $("#recommendation-state").textContent = capabilitiesFor(base).length ? "derivado de contratos" : "sem contrato assinado";

  renderCapabilities(base);
  renderContracts(base);
  renderOperation(base);
  renderAssessment(base);
  renderAuthority(base);
}

function showCapability(capability) {
  if (!capability) return;
  const detail = $("#details");
  detail.hidden = false;
  detail.innerHTML = `<h3>${esc(capability.title)}</h3><p class="detail-id">${esc(capability.id)} · capacidade operacional</p><div class="details-grid">
    <div class="detail-block"><strong>Propósito</strong><p>${esc(capability.purpose)}</p></div>
    <div class="detail-block"><strong>Processo</strong><p>${esc(capability.process)}</p></div>
    <div class="detail-block"><strong>Funções</strong><p>${esc((capability.functions || []).join(" · "))}</p></div>
    <div class="detail-block"><strong>Critérios</strong><p>${(capability.criteria || []).map(esc).join("<br>")}</p></div>
    <div class="detail-block"><strong>Contrato</strong><p>${(capability.contracts || capability.evidence || []).map(esc).join("<br>")}</p></div>
    <div class="detail-block"><strong>Observação</strong><p>${(capability.observations || []).map(esc).join("<br>") || "Nenhuma observação promovida."}</p></div>
  </div>
  <div class="detail-actions">
    <button type="button" data-execute-integration="${esc(capability.id)}" data-integration-version="${esc(capability.version || "1.0.0")}">Executar integração aprovada</button>
  </div>`;
  detail.querySelector("[data-execute-integration]")?.addEventListener("click", event => {
    executeIntegration(event.currentTarget);
  });
  detail.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function executeIntegration(button) {
  const integrationId = button.dataset.executeIntegration;
  const version = button.dataset.integrationVersion;
  const value = prompt("Valor de teste para executar a integração aprovada:", "sisTer-reflexivo");
  if (!value || !value.trim()) return;
  button.disabled = true;
  const response = await fetch(
    `/api/v1/engineering/integrations/${encodeURIComponent(integrationId)}/${encodeURIComponent(version)}/execute`,
    {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({value: value.trim()})
    }
  );
  if (!response.ok) {
    button.disabled = false;
    alert("Execução não registrada pela Base Operacional.");
    return;
  }
  const base = await fetchJsonOrFallback(
    "/api/v1/engineering/operational-base/current",
    emptyOperationalBase
  );
  render(base);
}

function renderAuthority(base) {
  $("#curation-content").innerHTML = `<div class="curation-grid">
    <div><strong>Recomendação</strong><p>${esc(base.assessment?.recommendation || "Sem recomendação persistida.")}</p></div>
    <div><strong>Decisão pendente</strong><p>${esc(base.assessment?.human_decision || "aprovar ou rejeitar integração candidata")}</p></div>
    <div><strong>Autoridade</strong><p>${esc(base.approval?.authority || "integration.approve")}</p><small>${esc(base.approval?.detail || "Decisão humana obrigatória.")}</small></div>
    <div><strong>Próxima configuração</strong><p>Somente uma decisão da engenharia pode transformar recomendação em nova configuração operacional.</p></div>
  </div>`;
}

async function fetchJsonOrFallback(url, fallback) {
  const response = await fetch(url);
  if (response.ok) return response.json();
  if (response.status === 401 || response.status === 403) {
    return { ...fallback, unavailable: true, unavailable_reason: "authentication_required" };
  }
  return fallback;
}

$("#refresh-ecosystem")?.addEventListener("click", loadEcosystem);
Promise.all([
  fetchJsonOrFallback("/api/v1/engineering/operational-base/current", emptyOperationalBase),
  loadEcosystem()
]).then(([operationalBase]) => render(operationalBase));
