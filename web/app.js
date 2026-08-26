const state = {
  ecosystem: {
    schema: "sister.runtime.ecosystem-view/1",
    composition_id: "",
    deployment_id: "",
    deployment_status: "N/D",
    systems: []
  },
  systems: [],
  contracts: [],
  evidence: [],
  services: [],
  currentUser: null
};

const qs = (selector, root = document) => root.querySelector(selector);
const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function systemInitials(name) {
  if (!name) return "ST";
  return name
    .split(/[\s_-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function statusSlug(status) {
  return String(status || "unknown")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, "-");
}

function normalizeParticipant(p) {
  const componentId = p.component_id || p.id || "unknown";
  const systemId = p.system_id || p.id || componentId;
  const transport = p.runtime?.transport || "N/D";
  const listen = p.runtime?.listen || "127.0.0.1";
  const port = p.runtime?.port || 0;
  const healthPath = p.probe?.health_path || "";
  const gatewayHost = p.gateway?.host || "";
  const gatewayPublicUrl = p.gateway?.public_url || p.gateway?.publicUrl || "";
  const healthStatus = p.health?.status || p.health_status || "not_observed";
  const healthHttpStatus = p.health?.http_status ?? p.health_http_status ?? 0;
  const healthDetail = p.health?.detail || p.health_detail || "not_observed";

  return {
    componentId,
    systemId,
    id: systemId,
    name: componentId.toUpperCase(),
    runtime: { transport, listen, port },
    probe: { healthPath },
    gateway: {
      host: gatewayHost,
      publicUrl: gatewayPublicUrl,
      public_url: gatewayPublicUrl
    },
    health: {
      status: healthStatus,
      httpStatus: healthHttpStatus,
      detail: healthDetail
    },
    healthStatus,
    healthHttpStatus,
    healthDetail
  };
}

async function loadEcosystem() {
  try {
    const response = await fetch("/api/ecosystem", { cache: "no-store" });
    if (response.ok) {
      const data = await response.json();
      state.ecosystem = data;
      state.systems = (Array.isArray(data.systems) ? data.systems : []).map(normalizeParticipant);
      return;
    }

    const fallbackResponse = await fetch("/api/systems", { cache: "no-store" });
    if (fallbackResponse.ok) {
      const rawSystems = await fallbackResponse.json();
      state.ecosystem = {
        schema: "sister.runtime.ecosystem-view/1",
        composition_id: "",
        deployment_id: "",
        deployment_status: "READY",
        systems: rawSystems
      };
      state.systems = (Array.isArray(rawSystems) ? rawSystems : []).map(normalizeParticipant);
      return;
    }
    throw new Error(`HTTP ${response.status}`);
  } catch {
    state.ecosystem = {
      schema: "sister.runtime.ecosystem-view/1",
      composition_id: "",
      deployment_id: "",
      deployment_status: "N/D",
      systems: []
    };
    state.systems = [];
  }
}

async function loadContracts() {
  try {
    const response = await fetch("/api/contracts", { cache: "no-store" });
    if (response.ok) {
      const data = await response.json();
      state.contracts = Array.isArray(data) ? data : [];
    } else {
      state.contracts = [];
    }
  } catch {
    state.contracts = [];
  }
}

async function loadEvidence() {
  try {
    const response = await fetch("/api/evidence", { cache: "no-store" });
    if (response.ok) {
      const data = await response.json();
      state.evidence = Array.isArray(data) ? data : [];
    } else {
      state.evidence = [];
    }
  } catch {
    state.evidence = [];
  }
}

async function loadDiagnostics() {
  try {
    const response = await fetch("/api/diagnostics", { cache: "no-store" });
    if (response.ok) {
      const data = await response.json();
      state.services = Array.isArray(data) ? data : [];
    } else {
      state.services = [];
    }
  } catch {
    state.services = [];
  }
}

function setCounts() {
  const participants = state.systems.length;
  const operational = state.systems.filter((s) => s.health.status === "online").length;
  const published = state.systems.filter((s) => Boolean(s.gateway.host)).length;
  const deployment = state.ecosystem.deployment_status || "N/D";

  const pEl = qs("#participant-count") || qs("#system-count");
  if (pEl) pEl.textContent = participants;

  const opEl = qs("#operational-count");
  if (opEl) opEl.textContent = operational;

  const pubEl = qs("#published-count");
  if (pubEl) pubEl.textContent = published;

  const depEl = qs("#deployment-status");
  if (depEl) depEl.textContent = deployment;
}

function renderSystems(filter = "") {
  const normalized = filter.trim().toLowerCase();
  const systems = state.systems.filter((system) => {
    const haystack = [
      system.componentId,
      system.systemId,
      system.runtime.transport,
      system.runtime.listen,
      String(system.runtime.port),
      system.probe.healthPath,
      system.gateway.host,
      system.health.status
    ].join(" ").toLowerCase();
    return haystack.includes(normalized);
  });

  const grid = qs("#systems-grid");
  if (!grid) return;

  if (systems.length === 0) {
    grid.innerHTML = `<p class="panel-note">Nenhum participante disponível ou correspondente à busca.</p>`;
    return;
  }

  grid.innerHTML = systems.map((system) => {
    const statusClass = system.health.status === "online"
      ? "online"
      : system.health.status === "offline"
        ? "offline"
        : "checking";

    const statusText = system.health.status === "online"
      ? "Online"
      : system.health.status === "offline"
        ? "Offline"
        : "Não observado";

    const runtimeBinding = system.runtime.port > 0
      ? `${escapeHtml(system.runtime.transport)} · ${escapeHtml(system.runtime.listen)}:${system.runtime.port}`
      : `${escapeHtml(system.runtime.transport)} · ${escapeHtml(system.runtime.listen)}`;

    const probeInfo = system.probe.healthPath
      ? `<code>${escapeHtml(system.probe.healthPath)}</code>`
      : `<span class="muted">Não declarado</span>`;

    const gatewayInfo = system.gateway.publicUrl
      ? `<a href="${escapeHtml(system.gateway.publicUrl)}" target="_blank" rel="noreferrer" class="gateway-link">${escapeHtml(system.gateway.host)} ↗</a>`
      : system.gateway.host
        ? `<span>${escapeHtml(system.gateway.host)}</span>`
        : `<span class="muted">Não publicado</span>`;

    return `
      <article class="system-card">
        <span class="system-mark" aria-hidden="true">${systemInitials(system.componentId)}</span>
        <div class="system-identity">
          <h4>
            ${escapeHtml(system.componentId.toUpperCase())}
            <span class="health-dot ${statusClass}" title="${statusText}"></span>
          </h4>
          <p class="system-meta">${escapeHtml(system.systemId)}</p>
        </div>
        <span class="status-pill" data-status="${statusSlug(system.health.status)}">${statusText}</span>
        <div class="system-facts">
          <div><span>Runtime</span><strong>${runtimeBinding}</strong></div>
          <div><span>Probe</span><strong>${probeInfo}</strong></div>
          <div><span>Gateway</span><strong>${gatewayInfo}</strong></div>
        </div>
        <div class="system-actions">
          <button class="text-link" type="button" data-participant-id="${escapeHtml(system.systemId)}">Ver detalhes →</button>
          ${system.gateway.publicUrl ? `<a class="text-link gateway-direct" href="${escapeHtml(system.gateway.publicUrl)}" target="_blank" rel="noreferrer">Abrir ↗</a>` : ""}
        </div>
      </article>
    `;
  }).join("");
}

function renderIntegrationBars() {
  const container = qs("#integration-bars");
  if (!container) return;

  const total = state.systems.length;
  if (total === 0) {
    container.innerHTML = `<p class="panel-note">Nenhum participante conectado para observação da rede.</p>`;
    return;
  }

  const operational = state.systems.filter((s) => s.health.status === "online").length;
  const bindings = state.systems.filter((s) => s.runtime.port > 0 || (s.runtime.transport && s.runtime.listen)).length;
  const probes = state.systems.filter((s) => Boolean(s.probe.healthPath)).length;
  const published = state.systems.filter((s) => Boolean(s.gateway.host)).length;

  const indicators = [
    { label: "Operacionais", count: operational, total, pct: Math.round((operational / total) * 100) },
    { label: "Bindings resolvidos", count: bindings, total, pct: Math.round((bindings / total) * 100) },
    { label: "Probes declarados", count: probes, total, pct: Math.round((probes / total) * 100) },
    { label: "Publicados no gateway", count: published, total, pct: Math.round((published / total) * 100) }
  ];

  container.innerHTML = indicators.map((item) => `
    <article class="result-item">
      <div class="result-row">
        <span>${escapeHtml(item.label)} (${item.count}/${item.total})</span>
        <strong>${item.pct}%</strong>
      </div>
      <div class="bar-track"><div class="bar-fill" style="width: ${item.pct}%"></div></div>
    </article>
  `).join("") + `
    <p class="panel-note">Proporções observadas em tempo real a partir da implantação declarativa ativa e health checks.</p>
  `;
}

function renderDiagnostics() {
  const container = qs("#diagnostic-grid");
  if (!container) return;

  if (state.services.length === 0) {
    container.innerHTML = `<p class="panel-note">Diagnósticos adicionais indisponíveis ou não configurados.</p>`;
    return;
  }

  container.innerHTML = state.services.map((service) => {
    const score = Number(service.score) || 0;
    const warn = score < 80 ? " warn" : "";
    return `
      <article class="diagnostic-card">
        <h3>${escapeHtml(service.service || service.name || "Serviço")}</h3>
        <p>${escapeHtml(service.summary || service.status || "")}</p>
        <div class="service-status">
          <span class="status-dot${warn}">${escapeHtml(service.status || "registrado")}</span>
          <strong>${score}%</strong>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width: ${score}%"></div></div>
      </article>
    `;
  }).join("");
}

function renderContracts() {
  const tbody = qs("#contracts-table");
  if (!tbody) return;

  if (state.contracts.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="panel-note">Nenhum contrato carregado.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.contracts.map((contract) => `
    <tr>
      <td>${escapeHtml(contract.name || contract.id || "Contrato")}</td>
      <td>${escapeHtml(contract.version || "N/D")}</td>
      <td>${escapeHtml(contract.required || "Opcional")}</td>
      <td>${escapeHtml(contract.rule || contract.description || "—")}</td>
    </tr>
  `).join("");
}

function renderEvidence() {
  const container = qs("#evidence-list");
  if (!container) return;

  if (state.evidence.length === 0) {
    container.innerHTML = `<p class="panel-note">Nenhuma evidência registrada.</p>`;
    return;
  }

  container.innerHTML = state.evidence.map((item) => `
    <article class="timeline-item">
      <time>${escapeHtml(item.time || item.created_at || "—")}</time>
      <div>
        <strong>${escapeHtml(item.source || "SisTer")} · ${escapeHtml(item.object || item.id || "")}</strong>
        <span>${escapeHtml(item.kind || "registro")} · ${escapeHtml(item.ref || "")}</span>
      </div>
      <span class="status-pill">${escapeHtml(item.status || "registrado")}</span>
    </article>
  `).join("");
}

function drawMap() {
  const canvas = qs("#territory-map");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#f8fbfd";
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = "#e1edf2";
  ctx.beginPath();
  ctx.moveTo(60, 275);
  ctx.bezierCurveTo(190, 120, 370, 250, 510, 105);
  ctx.bezierCurveTo(690, -10, 870, 90, 1010, 210);
  ctx.bezierCurveTo(910, 345, 690, 305, 530, 275);
  ctx.bezierCurveTo(335, 238, 210, 360, 60, 275);
  ctx.fill();

  ctx.strokeStyle = "#1a7dc4";
  ctx.lineWidth = 14;
  ctx.beginPath();
  ctx.moveTo(0, 92);
  ctx.bezierCurveTo(170, 135, 260, 65, 420, 105);
  ctx.bezierCurveTo(600, 150, 730, 245, 1100, 206);
  ctx.stroke();

  ctx.fillStyle = "#536a80";
  ctx.font = "900 13px Avenir, sans-serif";
  ctx.fillText(
    "Camadas: observacoes, evidencias, infraestrutura e contexto espacial",
    24,
    34
  );

  const systems = state.systems.slice(0, 4);

  if (systems.length === 0) {
    ctx.fillStyle = "#536a80";
    ctx.font = "700 18px Avenir, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(
      "Nenhum participante federado disponível",
      w / 2,
      h / 2
    );
    ctx.textAlign = "start";
    ctx.textBaseline = "alphabetic";
    return;
  }

  const boxWidth = 220;
  const boxHeight = 74;
  const gap = 22;
  const totalWidth = systems.length * boxWidth + (systems.length - 1) * gap;
  const startX = Math.max(24, (w - totalWidth) / 2);
  const y = 150;

  systems.forEach((system, index) => {
    const x = startX + index * (boxWidth + gap);
    const rawLabel = system.componentId ? system.componentId.toUpperCase() : system.systemId;
    const label = rawLabel.length > 25 ? `${rawLabel.slice(0, 24)}…` : rawLabel;

    ctx.fillStyle = "#d5e8f4";
    ctx.strokeStyle = "#062d55";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(x, y, boxWidth, boxHeight, 10);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#09254b";
    ctx.font = "900 16px Avenir, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, x + boxWidth / 2, y + boxHeight / 2);
  });

  if (state.systems.length > systems.length) {
    ctx.fillStyle = "#536a80";
    ctx.font = "700 13px Avenir, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(
      `+${state.systems.length - systems.length} participante(s)`,
      w / 2,
      y + boxHeight + 32
    );
  }

  ctx.textAlign = "start";
  ctx.textBaseline = "alphabetic";
}

function showToast(message) {
  const toast = qs("#toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 3200);
}

function showSystemDetails(systemId) {
  const system = state.systems.find(
    (item) => item.systemId === systemId || item.componentId === systemId || item.id === systemId
  );
  if (!system) return;

  const markEl = qs("#system-dialog-mark");
  if (markEl) markEl.textContent = systemInitials(system.componentId);

  const typeEl = qs("#system-dialog-type");
  if (typeEl) typeEl.textContent = `Componente: ${system.componentId}`;

  const titleEl = qs("#system-dialog-title");
  if (titleEl) titleEl.textContent = system.systemId;

  const statusText = system.health.status === "online"
    ? "Online (200 OK)"
    : system.health.status === "offline"
      ? `Offline (${system.health.detail || "falha de conexão"})`
      : `Não observado (${system.health.detail || "sem observação"})`;

  const probePath = system.probe.healthPath || "Não declarado";

  let gatewaySection = `<div><span>Gateway Host</span><strong>Não publicado</strong></div>`;
  let accessAction = `<span class="dialog-action dialog-action--disabled">Acesso via gateway não disponível</span>`;

  if (system.gateway.host) {
    gatewaySection = `
      <div><span>Gateway Host</span><strong>${escapeHtml(system.gateway.host)}</strong></div>
      <div><span>Public URL</span><strong>${system.gateway.publicUrl ? `<code>${escapeHtml(system.gateway.publicUrl)}</code>` : '<span class="muted">Não declarada</span>'}</strong></div>
    `;
  }

  if (system.gateway.publicUrl) {
    accessAction = `<a class="dialog-action" href="${escapeHtml(system.gateway.publicUrl)}" target="_blank" rel="noreferrer">Acessar via Gateway (${escapeHtml(system.gateway.host || system.componentId)}) ↗</a>`;
  }

  const contentEl = qs("#system-dialog-content");
  if (contentEl) {
    contentEl.innerHTML = `
      <div class="detail-section">
        <span>Identidade</span>
        <div class="detail-grid">
          <div><span>Component ID</span><strong>${escapeHtml(system.componentId)}</strong></div>
          <div><span>System ID</span><strong>${escapeHtml(system.systemId)}</strong></div>
        </div>
      </div>
      <div class="detail-section">
        <span>Runtime Binding</span>
        <div class="detail-grid">
          <div><span>Transporte</span><strong>${escapeHtml(system.runtime.transport)}</strong></div>
          <div><span>Endereço</span><strong>${escapeHtml(system.runtime.listen)}:${system.runtime.port}</strong></div>
        </div>
      </div>
      <div class="detail-section">
        <span>Observação de Health</span>
        <div class="detail-grid">
          <div><span>Probe Path</span><strong>${escapeHtml(probePath)}</strong></div>
          <div><span>Status</span><strong>${escapeHtml(statusText)}</strong></div>
          <div><span>HTTP Status</span><strong>${system.health.httpStatus}</strong></div>
          <div><span>Detalhe</span><strong>${escapeHtml(system.health.detail)}</strong></div>
        </div>
      </div>
      <div class="detail-section">
        <span>Publicação</span>
        <div class="detail-grid">
          ${gatewaySection}
        </div>
      </div>
      ${accessAction}
    `;
  }

  const dialog = qs("#system-dialog");
  if (dialog) dialog.showModal();
}

async function refreshState() {
  const btn = qs("#validate-button");
  if (btn) btn.disabled = true;
  showToast("Atualizando estado do ecossistema...");
  await loadEcosystem();
  setCounts();
  renderSystems(qs("#system-filter")?.value || "");
  renderIntegrationBars();
  drawMap();
  if (btn) btn.disabled = false;
  showToast("Estado do ecossistema atualizado.");
}

function bindNavigation() {
  qsa(".nav-link[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      qsa(".nav-link").forEach((item) => item.classList.remove("selected"));
      qsa(".view").forEach((item) => item.classList.remove("active"));
      button.classList.add("selected");
      const target = qs(`#view-${button.dataset.view}`);
      if (target) target.classList.add("active");
    });
  });
}

function showPublicIdentity() {
  state.currentUser = null;
  document.body.classList.remove("auth-pending", "authenticated-mode");
  document.body.classList.add("public-mode");
  qs("#public-home").hidden = false;
  qs("#authenticated-workspace").hidden = true;
  qs("#app-sidebar").hidden = true;
  qs("#auth-login").hidden = false;
  qs("#auth-identity").hidden = true;
  qs("#auth-avatar").hidden = true;
  qsa("[data-admin-only]").forEach((item) => {
    item.hidden = true;
  });
}

function showAuthenticatedIdentity(user) {
  state.currentUser = user;
  document.body.classList.remove("auth-pending", "public-mode");
  document.body.classList.add("authenticated-mode");
  qs("#public-home").hidden = true;
  qs("#authenticated-workspace").hidden = false;
  qs("#app-sidebar").hidden = false;
  qs("#auth-login").hidden = true;
  qs("#auth-identity").hidden = false;
  qs("#auth-avatar").hidden = false;
  qs("#auth-name").textContent = user.name;
  qs("#auth-avatar").textContent = systemInitials(user.name);
  if (user.role === "admin") {
    qsa("[data-admin-only]").forEach((item) => {
      item.hidden = false;
    });
  }
}

async function initializeIdentity() {
  try {
    const response = await fetch("/api/me", { cache: "no-store" });
    if (response.status === 401) {
      showPublicIdentity();
      return;
    }
    if (!response.ok) throw new Error();
    showAuthenticatedIdentity(await response.json());
  } catch {
    showPublicIdentity();
  }
}

async function logout() {
  await fetch("/api/auth/logout", { method: "POST" }).catch(() => { });
  window.location.href = "/";
}

async function init() {
  await Promise.all([
    loadEcosystem(),
    loadContracts(),
    loadEvidence(),
    loadDiagnostics()
  ]);

  setCounts();
  renderSystems();
  renderIntegrationBars();
  renderDiagnostics();
  renderContracts();
  renderEvidence();
  drawMap();
  bindNavigation();

  qs("#system-filter")?.addEventListener("input", (event) => renderSystems(event.target.value));
  qs("#validate-button")?.addEventListener("click", refreshState);
  qs("#systems-grid")?.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-participant-id]") || event.target.closest("[data-system-id]");
    if (trigger) showSystemDetails(trigger.dataset.participantId || trigger.dataset.systemId);
  });
  qs("#system-dialog-close")?.addEventListener("click", () => qs("#system-dialog")?.close());
  qs("#system-dialog")?.addEventListener("click", (event) => {
    if (event.target === qs("#system-dialog")) qs("#system-dialog")?.close();
  });
  qs("#auth-logout")?.addEventListener("click", logout);
  initializeIdentity();
}

init();