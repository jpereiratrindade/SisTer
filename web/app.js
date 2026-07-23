const state = {
  systems: [
    {
      id: "morfocampo",
      name: "MorfoCampo",
      version: "0.2.1",
      owner: "Equipe Campo",
      type: "Campo",
      status: "Operacional",
      description: "Sistema de campo para observacoes, evidencias locais e sincronizacao offline por contrato.",
      contract: "sister-contracts/0.1.0",
      accessUrl: "https://127.0.0.1:8011",
      accessMode: "Restrito",
      publicScope: "Indicadores agregados",
      restrictedScope: "Observacoes e metadados",
      privateScope: "Midia bruta e notas",
      domains: ["campo_nativo", "silvipastoril", "observacao_campo"],
      modes: ["offline", "local_network", "camponode"],
      exports: ["observations", "evidence", "photos", "field_notes", "spatial_context"],
      policy: ["proveniencia", "schema", "offline"],
      infra: {
        availability: "98%",
        response: "sync 12 min",
        storage: "41%",
        lastCheck: "09:20",
        signal: "ok"
      }
    },
    {
      id: "droneops",
      name: "DroneOps",
      version: "0.1.0",
      owner: "Equipe Geoespacial",
      type: "Missao",
      status: "Em validacao",
      description: "Organiza missoes, registros de voo e evidencias georreferenciadas para leitura territorial.",
      contract: "sister-contracts/0.1.0",
      accessUrl: "https://127.0.0.1:8012",
      accessMode: "Restrito",
      publicScope: "Cobertura generalizada",
      restrictedScope: "Camadas e logs resumidos",
      privateScope: "Imagens brutas e operador",
      domains: ["drone", "imageamento", "missao_campo", "evidencia_geoespacial"],
      modes: ["offline", "local_network", "pwa"],
      exports: ["mission_plan", "flight_log", "images", "spatial_layers", "evidence_package"],
      policy: ["proveniencia", "schema", "operador", "referencia_espacial"],
      infra: {
        availability: "91%",
        response: "sync 28 min",
        storage: "63%",
        lastCheck: "09:12",
        signal: "warn"
      }
    },
    {
      id: "camponode",
      name: "CampoNode",
      version: "0.1.0",
      owner: "Infraestrutura",
      type: "Infraestrutura",
      status: "Planejado",
      description: "No local para cache, sincronizacao e continuidade operacional quando a conectividade oscila.",
      contract: "sister-contracts/0.1.0",
      accessUrl: "https://camponode.local",
      accessMode: "Rede local",
      publicScope: "Status agregado",
      restrictedScope: "Saude do no e cache",
      privateScope: "Logs operacionais",
      domains: ["rede_local", "armazenamento", "sincronizacao"],
      modes: ["offline", "local_network", "edge"],
      exports: ["sync_log", "node_health", "package_cache"],
      policy: ["proveniencia", "schema", "auditoria"],
      infra: {
        availability: "N/D",
        response: "planejado",
        storage: "N/D",
        lastCheck: "sem coleta",
        signal: "planned"
      }
    },
    {
      id: "radar_sister_resiliencia",
      name: "Radar-Sister Resiliencia",
      version: "0.1.0",
      owner: "Equipe Resiliencia",
      type: "Analitico",
      status: "Operacional",
      description: "Modulo analitico para triagem, scores, shortlists e inteligencia territorial auditavel.",
      contract: "sister-contracts/0.1.0",
      accessUrl: "http://127.0.0.1:8765",
      accessMode: "Local",
      publicScope: "Links publicos e scores agregados",
      restrictedScope: "Shortlists, scores e trilhas",
      privateScope: "Sessoes, chaves e revisoes brutas",
      domains: ["resiliencia", "inteligencia_territorial", "adaptacao_climatica"],
      modes: ["local_gui", "local_cli", "postgresql_pgvector"],
      exports: ["normalized_metadata", "scores_jsonl", "shortlist_markdown", "audit_log", "vector_chunks"],
      policy: ["proveniencia", "schema", "operador", "vetorial"],
      infra: {
        availability: "96%",
        response: "127 ms",
        storage: "52%",
        lastCheck: "09:15",
        signal: "ok"
      }
    },
    {
      id: "sister_studio",
      name: "Sister-Studio",
      version: "0.2.1",
      owner: "Laboratorio SisTer",
      type: "Criativo",
      status: "Integrado",
      description: "Estudio audiovisual conectado por contrato para composicao, voz e video, com dados privados preservados no produtor.",
      contract: "sister-studio.integration/1.0.0",
      accessUrl: "https://127.0.0.1:8443",
      accessMode: "Local",
      publicScope: "Identidade e versao do sistema",
      restrictedScope: "Capacidades, formatos e saude sanitizada",
      privateScope: "Identidade, voz, texto, midia, projetos e auditoria",
      domains: ["audio", "musica_procedural", "voz", "tts", "video", "midi", "wav", "ogg", "srt", "mp4"],
      modes: ["local_web", "local_network", "authenticated_api", "isolated_inference"],
      exports: ["capability_catalog", "supported_format_matrix", "sanitized_service_health"],
      policy: ["proveniencia", "schema", "minimizacao", "tls", "privacidade"],
      infra: {
        availability: "consultando",
        response: "HTTPS",
        storage: "não compartilhado",
        lastCheck: "sob demanda",
        signal: "ok"
      }
    }
  ],
  contracts: [
    {
      name: "System Manifest",
      version: "0.1.0",
      required: "Sim",
      rule: "Todo sistema federado declara identidade, dominio, modos operacionais, exports e politica de dados."
    },
    {
      name: "CampoSync Package",
      version: "0.1.0",
      required: "Para ingestao offline",
      rule: "Pacote precisa conter origem, contrato, conteudo declarado, data de criacao e checksum."
    },
    {
      name: "Sister-Studio Integration",
      version: "1.0.0",
      required: "Para capacidades criativas",
      rule: "Somente capacidades e saude sanitizada; conteudo e identidade permanecem no Studio."
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
      time: "2026-07-09 21:30",
      source: "MorfoCampo",
      object: "obs-001",
      kind: "photo",
      ref: "evidence/photos/obs-001.jpg",
      status: "proveniencia minima"
    },
    {
      time: "2026-07-09 21:42",
      source: "DroneOps",
      object: "mission-terrace-01",
      kind: "spatial_layer",
      ref: "evidence/layers/orthomosaic.geojson",
      status: "referencia espacial"
    },
    {
      time: "2026-07-09 22:05",
      source: "SisTer Core",
      object: "pkg-camposync-001",
      kind: "log",
      ref: "audit/validation_report.json",
      status: "schema validado"
    },
    {
      time: "2026-07-10 09:15",
      source: "Radar-Sister Resiliencia",
      object: "shortlist-resiliencia-001",
      kind: "document",
      ref: "data/exports/*_shortlist.md",
      status: "triagem auditavel"
    }
  ],
  integrationResults: [
    { label: "Manifestos reconhecidos", value: 100 },
    { label: "Proveniencia minima", value: 96 },
    { label: "Cobertura CampoSync", value: 82 },
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
      name: "Package Ingest",
      summary: "Entrada de pacotes CampoSync e validacao de manifesto.",
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

  if (localNames.has(url.hostname) || url.hostname.endsWith(".local")) {
    url.hostname = window.location.hostname;
  }

  return url.href.replace(/\/$/, "");
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

  qs("#systems-grid").innerHTML = systems.map((system) => `
    <article class="system-card">
      <span class="system-mark" aria-hidden="true">${systemInitials(system.name)}</span>
      <div class="system-identity">
        <h4>${system.name}</h4>
        <p class="system-meta">${system.type} · ${system.owner}</p>
      </div>
      <span class="status-pill" data-status="${statusSlug(system.status)}">${system.status}</span>
      <p class="system-description">${system.description}</p>
      <div class="system-actions">
        <button class="text-link" type="button" data-system-id="${system.id}">Conhecer sistema →</button>
      </div>
    </article>
  `).join("") || `
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

function integrationErrorDetail(code) {
  const messages = {
    integration_configuration_unavailable: "Credencial ou certificado do Studio ainda não foram provisionados.",
    studio_unavailable: "O gateway do Sister-Studio não respondeu.",
    studio_identity_not_verified: "A identidade TLS do Sister-Studio não foi validada.",
    studio_contract_request_failed: "O Studio recusou ou não concluiu a consulta contratual.",
    studio_contract_invalid: "A resposta não corresponde ao contrato reconhecido.",
    trust_configuration_failed: "A autoridade certificadora configurada não pôde ser carregada.",
    tls_initialization_failed: "O cliente TLS do SisTer não pôde ser inicializado."
  };
  return messages[code] || "A integração está indisponível sem expor detalhes internos.";
}

async function loadSisterStudioIntegration() {
  const title = qs("#studio-connection-title");
  const detail = qs("#studio-connection-detail");
  const signal = qs("#studio-signal");
  title.textContent = "Consultando Sister-Studio…";
  detail.textContent = "Validando TLS, credencial e versão do contrato.";
  signal.className = "connection-signal loading";
  try {
    const response = await fetch("/api/integrations/sister-studio", {cache: "no-store"});
    if (!response.ok) throw new Error("request_failed");
    const payload = await response.json();
    if (payload.status !== "connected") {
      title.textContent = payload.status === "not_configured" ? "Integração não configurada" : "Sister-Studio indisponível";
      detail.textContent = integrationErrorDetail(payload.error_code);
      signal.className = "connection-signal error";
      return;
    }

    const {capabilities, health} = payload;
    title.textContent = health.status === "ok" ? "Conectado e operacional" : "Conectado com módulos indisponíveis";
    detail.textContent = "Contrato remoto autenticado e conteúdo pessoal ausente na resposta.";
    signal.className = `connection-signal ${health.status === "ok" ? "online" : "warning"}`;
    qs("#studio-contract-version").textContent = `integration/${capabilities.contract_version}`;
    qs("#studio-system-version").textContent = `${capabilities.system.name} ${capabilities.system.version}`;
    qs("#studio-checked-at").textContent = new Date(health.checked_at).toLocaleString("pt-BR");
    qs("#studio-modules").innerHTML = health.modules.map((module) => `
      <article>
        <span class="connection-signal ${module.status === "available" ? "online" : "error"}"></span>
        <div><strong>${escapeHtml(module.id)}</strong><small>${module.status === "available" ? "Disponível" : "Offline"}</small></div>
      </article>
    `).join("");
    qs("#studio-capabilities").innerHTML = capabilities.capabilities.map((capability) => `
      <article>
        <div><strong>${escapeHtml(capability.name)}</strong><small>${escapeHtml(capability.id)}</small></div>
        <span>${capability.outputs.map(escapeHtml).join(" · ")}</span>
      </article>
    `).join("");

    const studio = state.systems.find((system) => system.id === "sister_studio");
    studio.version = capabilities.system.version;
    studio.status = health.status === "ok" ? "Integrado" : "Degradado";
    studio.infra.availability = health.status;
    studio.infra.lastCheck = new Date(health.checked_at).toLocaleTimeString("pt-BR");
    renderSystems(qs("#system-filter").value);
  } catch {
    title.textContent = "Não foi possível consultar a integração";
    detail.textContent = "Entre novamente como administrador e tente atualizar.";
    signal.className = "connection-signal error";
  }
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

  const plots = [
    { x: 230, y: 168, w: 155, h: 82, color: "#b9dfd8", label: "MorfoCampo" },
    { x: 480, y: 120, w: 180, h: 86, color: "#d5e8f4", label: "DroneOps" },
    { x: 705, y: 220, w: 170, h: 74, color: "#e9d199", label: "CampoNode" }
  ];

  plots.forEach((plot) => {
    ctx.fillStyle = plot.color;
    ctx.strokeStyle = "#062d55";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(plot.x, plot.y, plot.w, plot.h, 10);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#09254b";
    ctx.font = "900 17px Avenir, sans-serif";
    ctx.fillText(plot.label, plot.x + 18, plot.y + 44);
  });

  const points = [
    { x: 292, y: 210, label: "M01", color: "#1c9b98" },
    { x: 560, y: 164, label: "D01", color: "#1a7dc4" },
    { x: 786, y: 258, label: "N01", color: "#e8a733" }
  ];

  points.forEach((point) => {
    ctx.fillStyle = point.color;
    ctx.beginPath();
    ctx.arc(point.x, point.y, 13, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.font = "900 11px Avenir, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(point.label, point.x, point.y);
  });

  ctx.textAlign = "start";
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#536a80";
  ctx.font = "900 13px Avenir, sans-serif";
  ctx.fillText("Camadas: observacoes, evidencias, infraestrutura e contexto espacial", 24, 34);
}

function showToast(message) {
  const toast = qs("#toast");
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 3200);
}

function validateSample() {
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
  const accessUrl = resolveAccessUrl(system.accessUrl);

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
    </div>
    <div class="detail-section">
      <span>Domínios</span>
      <div class="tag-row">${system.domains.map((item) => `<span class="tag">${item}</span>`).join("")}</div>
    </div>
    <div class="detail-section">
      <span>Entregas para o SisTer</span>
      <div class="tag-row">${system.exports.map((item) => `<span class="tag">${item}</span>`).join("")}</div>
    </div>
    <div class="detail-section">
      <span>Compartilhamento</span>
      <div class="detail-grid">
        <div><span>Público</span><strong>${system.publicScope}</strong></div>
        <div><span>Restrito</span><strong>${system.restrictedScope}</strong></div>
      </div>
    </div>
    ${system.status === "Planejado"
      ? `<span class="dialog-action dialog-action--disabled">Acesso ainda não disponível</span>`
      : `<a class="dialog-action" href="${accessUrl}" target="_blank" rel="noreferrer">Acessar subsistema</a>`}
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
      if (button.dataset.view === "studio") loadSisterStudioIntegration();
    });
  });
}

function showPublicIdentity() {
  qs("#auth-login").hidden = false;
  qs("#auth-identity").hidden = true;
  qs("#auth-avatar").hidden = true;
  qsa("[data-admin-only]").forEach((item) => {
    item.hidden = true;
  });
}

function showAuthenticatedIdentity(user) {
  qs("#auth-login").hidden = true;
  qs("#auth-identity").hidden = false;
  qs("#auth-avatar").hidden = false;
  qs("#auth-name").textContent = user.name;
  qs("#auth-avatar").textContent = systemInitials(user.name);
  if (user.role === "admin") {
    qsa("[data-admin-only]").forEach((item) => {
      item.hidden = false;
    });
    loadSisterStudioIntegration();
  }
}

async function initializeIdentity() {
  try {
    const response = await fetch("/api/me", {cache: "no-store"});
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
  await fetch("/api/auth/logout", {method: "POST"}).catch(() => {});
  window.location.href = "/";
}

function init() {
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
  qs("#studio-refresh").addEventListener("click", loadSisterStudioIntegration);
  initializeIdentity();
}

init();
