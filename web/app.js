const state = {
  systems: [],
  contracts: [
    {
      name: "System Manifest",
      version: "0.1.0",
      required: "Sim",
      rule: "Todo sistema federado declara identidade, dominio, modos operacionais, exports e politica de dados."
    },
    {
      name: "Reference Subsystem",
      version: "0.1.0",
      required: "Para validação do núcleo",
      rule: "Alvo único, parametrizado, interno e mediado pelo SisTer."
    },
    {
      name: "Evidence",
      version: "0.1.0",
      required: "Para dado promovido",
      rule: "Evidencia vincula sistema produtor, objeto, tipo, URI, momento de captura e checksum quando aplicavel."
    }
  ],
  evidence: [
    {
      time: "2026-07-09 22:05",
      source: "SisTer Core",
      object: "reference-contract-001",
      kind: "log",
      ref: "audit/validation_report.json",
      status: "schema validado"
    }
  ],
  integrationResults: [
    { label: "Manifestos reconhecidos", value: 100 },
    { label: "Proveniencia minima", value: 96 },
    { label: "Cobertura da API canônica", value: 100 },
    { label: "Prontidao para catalogo", value: 74 }
  ],
  services: [
    {
      name: "Contract Registry",
      summary: "Schemas, versoes e compatibilidade de contratos.",
      status: "operacional",
      score: 100
    },
    {
      name: "Conformance Runner",
      summary: "Validação das rotas, identidade, transporte e falhas da referência.",
      status: "em validacao",
      score: 78
    },
    {
      name: "Evidence Store",
      summary: "Rastreio de evidencias, checksums e referencias externas.",
      status: "operacional",
      score: 92
    },
    {
      name: "Territorial Catalog",
      summary: "Promocao de objetos territoriais confiaveis.",
      status: "planejado",
      score: 45
    },
    {
      name: "API Server",
      summary: "Exposicao REST para UI, integracoes locais e auditoria.",
      status: "planejado",
      score: 32
    },
    {
      name: "Governance Monitor",
      summary: "Sinais de ADR, DDD, DAI, politicas, LGPD e seguranca.",
      status: "operacional",
      score: 88
    }
  ]
};

const qs = (selector, root = document) => root.querySelector(selector);
const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];


function normalizeSystem(system) {
  const accessUrl = system.accessUrl ?? system.access_url ?? null;
  return {
    id: system.id ?? "unknown",
    name: system.name ?? system.id ?? "Subsistema",
    version: system.version ?? "N/D",
    owner: system.owner ?? "Responsável não declarado",
    type: system.type ?? "Subsistema federado",
    status: system.status ?? "Registrado",
    description: system.description ?? "Subsistema registrado no ecossistema SisTer.",
    contract: system.contract ?? "Contrato não declarado",
    governanceContract: system.governanceContract ?? system.governance_contract ?? null,
    accessUrl,
    healthStatus: system.healthStatus ?? system.health_status ?? "unknown",
    healthObservedBy: system.healthObservedBy ?? system.health_observed_by ?? null,
    healthHttpStatus: system.healthHttpStatus ?? system.health_http_status ?? 0,
    healthDetail: system.healthDetail ?? system.health_detail ?? null,
    accessMode: system.accessMode ?? system.access_mode ?? "Acesso governado",
    accessRestricted: system.accessRestricted ?? system.access_restricted ?? false,
    publicScope: system.publicScope ?? system.public_scope ?? "Não declarado",
    restrictedScope: system.restrictedScope ?? system.restricted_scope ?? "Não declarado",
    privateScope: system.privateScope ?? system.private_scope ?? "Não declarado",
    domains: Array.isArray(system.domains) ? system.domains : [],
    modes: Array.isArray(system.modes) ? system.modes : [],
    exports: Array.isArray(system.exports) ? system.exports : [],
    policy: Array.isArray(system.policy) ? system.policy : [],
    dataReferences: Array.isArray(system.dataReferences) ? system.dataReferences : [],
    dataSummary: system.dataSummary ?? ""
  };
}

async function loadSystems() {
  try {
    const response = await fetch("/api/systems", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const systems = await response.json();
    if (!Array.isArray(systems)) throw new Error("invalid systems catalog");
    state.systems = systems.map(normalizeSystem);
  } catch {
    state.systems = [];
  }
}

function setCounts() {
  qs("#signed-contract-count").textContent = state.systems.length;
  qs("#system-count").textContent = state.systems.length;
  qs("#evidence-count").textContent = state.evidence.length;
  qs("#integration-compliance").textContent = "N/D";
}

function systemInitials(name) {
  return name
    .split(/[\s_-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function statusSlug(status) {
  return status
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, "-");
}

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value);
  return element.innerHTML;
}

function resolveAccessUrl(accessUrl) {
  const url = new URL(accessUrl, window.location.href);
  const localNames = new Set(["127.0.0.1", "localhost", "0.0.0.0"]);

  if ((localNames.has(url.hostname) || url.hostname.endsWith(".local")) && !url.port) {
    url.hostname = window.location.hostname;
  }

  return url.href.replace(/\/$/, "");
}

function resolveSystemAccessUrl(system) {
  if (!system.accessUrl) return null;
  const url = new URL(resolveAccessUrl(system.accessUrl));
  return url.href.replace(/\/$/, "");
}

function rerenderSystems() {
  renderSystems(qs("#system-filter")?.value || "");
}

function renderSystems(filter = "") {
  const normalized = filter.trim().toLowerCase();
  const systems = state.systems.filter((system) => {
    const haystack = [
      system.name,
      system.id,
      system.type,
      system.status,
      system.contract,
      ...system.domains,
      ...system.modes,
      ...system.exports,
      ...system.policy
    ].join(" ").toLowerCase();
    return haystack.includes(normalized);
  });

  qs("#systems-grid").innerHTML = systems.map((system) => {
    const dataReference = system.dataReferences?.length
      ? `
        <p class="system-data-reference">
          <span>Dados:</span> ${escapeHtml(system.dataSummary)} ·
          ${system.dataReferences.map((source) => `
            <a href="${source.url}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.label)}</a>
          `).join(" · ")}
        </p>
      `
      : "";
    return `
    <article class="system-card">
      <span class="system-mark" aria-hidden="true">${systemInitials(system.name)}</span>
      <div class="system-identity">
        <h4>
          ${system.name}
          ${system.healthStatus === 'online' ? '<span class="health-dot online" title="Online"></span>' : ''}
          ${system.healthStatus === 'offline' ? '<span class="health-dot offline" title="Offline"></span>' : ''}
          ${system.healthStatus === 'unknown' || !system.healthStatus ? '<span class="health-dot checking" title="Estado não observado"></span>' : ''}
        </h4>
        <p class="system-meta">${system.type} · ${system.owner}</p>
      </div>
      <span class="status-pill" data-status="${statusSlug(system.status)}">${system.status}</span>
      <p class="system-description">${system.description}</p>
      ${dataReference}
      <div class="system-actions">
        <button class="text-link" type="button" data-system-id="${system.id}">Conhecer sistema →</button>
      </div>
    </article>
  `;
  }).join("") || `
    <p class="panel-note">Nenhum subsistema corresponde à busca.</p>
  `;
}

function renderIntegrationBars() {
  qs("#integration-bars").innerHTML = state.integrationResults.map((item) => `
    <article class="result-item">
      <div class="result-row"><span>${item.label}</span><strong>${item.value}%</strong></div>
      <div class="bar-track"><div class="bar-fill" style="width: ${item.value}%"></div></div>
    </article>
  `).join("") + `
    <p class="panel-note">Indicadores demonstrativos. A aferição automatizada será produzida pelos validadores do ecossistema.</p>
  `;
}

function renderDiagnostics() {
  qs("#diagnostic-grid").innerHTML = state.services.map((service) => {
    const warn = service.score < 80 ? " warn" : "";
    return `
      <article class="diagnostic-card">
        <h3>${service.name}</h3>
        <p>${service.summary}</p>
        <div class="service-status">
          <span class="status-dot${warn}">${service.status}</span>
          <strong>${service.score}%</strong>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width: ${service.score}%"></div></div>
      </article>
    `;
  }).join("");
}

function renderContracts() {
  qs("#contracts-table").innerHTML = state.contracts.map((contract) => `
    <tr>
      <td>${contract.name}</td>
      <td>${contract.version}</td>
      <td>${contract.required}</td>
      <td>${contract.rule}</td>
    </tr>
  `).join("");
}

function renderEvidence() {
  qs("#evidence-list").innerHTML = state.evidence.map((item) => `
    <article class="timeline-item">
      <time>${item.time}</time>
      <div>
        <strong>${item.source} · ${item.object}</strong>
        <span>${item.kind} · ${item.ref}</span>
      </div>
      <span class="status-pill">${item.status}</span>
    </article>
  `).join("");
}

function drawMap() {
  const canvas = qs("#territory-map");
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
      "Nenhum subsistema federado disponível",
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
  const totalWidth =
    systems.length * boxWidth + (systems.length - 1) * gap;
  const startX = Math.max(24, (w - totalWidth) / 2);
  const y = 150;

  systems.forEach((system, index) => {
    const x = startX + index * (boxWidth + gap);
    const rawLabel = system.name || system.id || "Subsistema";
    const label =
      rawLabel.length > 25
        ? `${rawLabel.slice(0, 24)}…`
        : rawLabel;

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
      `+${state.systems.length - systems.length} subsistema(s)`,
      w / 2,
      y + boxHeight + 32
    );
  }

  ctx.textAlign = "start";
  ctx.textBaseline = "alphabetic";
}

function showToast(message) {
  const toast = qs("#toast");
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 3200);
}

function validateSample() {
  if (state.systems.length === 0) {
    showToast("Nenhum subsistema federado disponível para validação.");
    return;
  }

  const invalid = state.systems.filter((system) => {
    return !system.id || !system.name || !system.contract || system.domains.length === 0 || !system.policy.includes("proveniencia");
  });

  if (invalid.length === 0) {
    showToast("Amostra valida: contrato, dominio, proveniencia e politica declarados.");
  } else {
    showToast(`Amostra com pendencias: ${invalid.map((system) => system.name).join(", ")}`);
  }
}

function showSystemDetails(systemId) {
  const system = state.systems.find((item) => item.id === systemId);
  if (!system) return;
  const accessUrl = resolveSystemAccessUrl(system);
  const governanceDetail = system.governanceContract
    ? `<div><span>Governança</span><strong>${system.governanceContract}</strong></div>`
    : "";
  const dataReferences = system.dataReferences?.length
    ? `
      <div class="detail-section">
        <span>Dados e fontes</span>
        <p class="dialog-data-summary">${escapeHtml(system.dataSummary)}</p>
        <div class="tag-row">
          ${system.dataReferences.map((source) => `
            <a class="tag tag--link" href="${source.url}" target="_blank" rel="noopener noreferrer">
              ${escapeHtml(source.label)} ↗
            </a>
          `).join("")}
        </div>
      </div>
    `
    : "";
  let accessAction = `<a class="dialog-action" href="${accessUrl}" target="_blank" rel="noreferrer">Acessar subsistema</a>`;
  if (system.status === "Planejado") {
    accessAction = `<span class="dialog-action dialog-action--disabled">Acesso ainda não disponível</span>`;
  } else if (system.accessRestricted && !accessUrl) {
    accessAction = state.currentUser
      ? `<span class="dialog-action dialog-action--disabled">Acesso restrito indisponível</span>`
      : `<a class="dialog-action" href="/login">Entrar para acessar</a>`;
  } else if (system.healthStatus === "offline") {
    accessAction = `<span class="dialog-action dialog-action--disabled">Subsistema temporariamente indisponível</span>`;
  } else if (system.healthStatus === "checking") {
    accessAction = `<span class="dialog-action dialog-action--disabled">Verificando disponibilidade...</span>`;
  }

  qs("#system-dialog-mark").textContent = systemInitials(system.name);
  qs("#system-dialog-type").textContent = `${system.type} · ${system.status}`;
  qs("#system-dialog-title").textContent = system.name;
  qs("#system-dialog-content").innerHTML = `
    <p class="dialog-summary">${system.description}</p>
    <div class="detail-grid">
      <div><span>Versão</span><strong>${system.version}</strong></div>
      <div><span>Responsável</span><strong>${system.owner}</strong></div>
      <div><span>Acesso</span><strong>${system.accessMode}</strong></div>
      <div><span>Contrato</span><strong>${system.contract}</strong></div>
      ${governanceDetail}
    </div>
    <div class="detail-section">
      <span>Domínios</span>
      <div class="tag-row">${system.domains.map((item) => `<span class="tag">${item}</span>`).join("")}</div>
    </div>
    <div class="detail-section">
      <span>Entregas para o SisTer</span>
      <div class="tag-row">${system.exports.map((item) => `<span class="tag">${item}</span>`).join("")}</div>
    </div>
    ${dataReferences}
    <div class="detail-section">
      <span>Compartilhamento</span>
      <div class="detail-grid">
        <div><span>Público</span><strong>${system.publicScope}</strong></div>
        <div><span>Restrito</span><strong>${system.restrictedScope}</strong></div>
        <div><span>Privado</span><strong>${system.privateScope}</strong></div>
      </div>
    </div>
    ${accessAction}
  `;
  qs("#system-dialog").showModal();
}

function bindNavigation() {
  qsa(".nav-link[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      qsa(".nav-link").forEach((item) => item.classList.remove("selected"));
      qsa(".view").forEach((item) => item.classList.remove("active"));
      button.classList.add("selected");
      qs(`#view-${button.dataset.view}`).classList.add("active");
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
  await loadSystems();
  setCounts();
  renderSystems();
  renderIntegrationBars();
  renderDiagnostics();
  renderContracts();
  renderEvidence();
  drawMap();
  bindNavigation();

  qs("#system-filter").addEventListener("input", (event) => renderSystems(event.target.value));
  qs("#validate-button").addEventListener("click", validateSample);
  qs("#systems-grid").addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-system-id]");
    if (trigger) showSystemDetails(trigger.dataset.systemId);
  });
  qs("#system-dialog-close").addEventListener("click", () => qs("#system-dialog").close());
  qs("#system-dialog").addEventListener("click", (event) => {
    if (event.target === qs("#system-dialog")) qs("#system-dialog").close();
  });
  qs("#auth-logout").addEventListener("click", logout);
  initializeIdentity();
}

init();